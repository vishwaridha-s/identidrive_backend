from django.shortcuts import render

import os
import uuid
import json
from django.conf import settings
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services.video import extract_frames
from .services.detector import detect_plates
from .ocr_utils import recognize_plate
from .models import PlatePrediction

# ---------------------------
# Upload Video
# ---------------------------
@api_view(['POST'])
def upload_video(request):
    video = request.FILES.get("video")

    if not video:
        return Response({"error": "No video uploaded"}, status=400)

    video_path = os.path.join(settings.MEDIA_ROOT, video.name)

    with open(video_path, "wb+") as f:
        for chunk in video.chunks():
            f.write(chunk)

    folder_name, frames = extract_frames(video_path, settings.MEDIA_ROOT)

    frame_urls = [
        f"{settings.MEDIA_URL}{folder_name}/{os.path.basename(frame)}"
        for frame in frames
    ]

    video_url = f"{settings.MEDIA_URL}{video.name}"

    return Response({
        "frames": frame_urls,
        "video_url": video_url
    })


# ---------------------------
# Detect Plates (bounding box only)
# ---------------------------
@api_view(['POST'])
def detect_plates_view(request):
    frame_url = request.data.get("frame_url")

    if not frame_url:
        return Response({"error": "No frame selected"}, status=400)

    frame_path = os.path.join(
        settings.MEDIA_ROOT,
        frame_url.replace(settings.MEDIA_URL, "").lstrip("/")
    )

    boxes = detect_plates(frame_path)

    return Response({"boxes": boxes})


# ---------------------------
# Recognize Plate (OCR)
# ---------------------------
@api_view(['POST'])
def recognize_plate_view(request):

    try:
        data = request.data

        frame_url = data.get("frame_url")

        x1 = int(float(data.get("x1", 0)))
        y1 = int(float(data.get("y1", 0)))
        x2 = int(float(data.get("x2", 0)))
        y2 = int(float(data.get("y2", 0)))

        frame_path = os.path.join(
            settings.MEDIA_ROOT,
            frame_url.replace(settings.MEDIA_URL, "").lstrip("/")
        )

        result = recognize_plate(frame_path, x1, y1, x2, y2)

        if "error" in result:

            return Response({
                "plate_number": result["error"],
                "confidence": 0,
                "is_error": True
            })

        text = result["plate_number"]
        conf = result["confidence"]

        PlatePrediction.objects.create(
            video_name=os.path.basename(frame_url),
            frame_path=frame_url,
            top1=text,
            confidence=conf
        )

        return Response({
            "plate_number": text,
            "confidence": conf,
            "is_error": False
        })

    except Exception as e:

        print("OCR CRITICAL ERROR:", str(e))

        return Response({
            "plate_number": "PROCESSOR ERROR",
            "confidence": 0,
            "is_error": True
        })

# ---------------------------
# Capture Current Frame
# ---------------------------
@api_view(['POST'])
def capture_frame(request):
    frame = request.FILES.get("frame")

    if not frame:
        return Response({"error": "No frame uploaded"}, status=400)

    folder = "captured_frames"
    folder_path = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(folder_path, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(folder_path, filename)

    with open(file_path, "wb+") as f:
        for chunk in frame.chunks():
            f.write(chunk)

    frame_url = f"{settings.MEDIA_URL}{folder}/{filename}"

    return Response({"frame_url": frame_url})


# ---------------------------
# History Filter
# ---------------------------
@api_view(['GET'])
def get_predictions(request):
    date = request.GET.get("date")

    queryset = PlatePrediction.objects.all().order_by("-created_at")

    if date:
        parsed_date = parse_date(date)
        if parsed_date:
            queryset = queryset.filter(created_at__date=parsed_date)

    data = [
        {
            "video_name": p.video_name,
            "top1": p.top1,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "confidence": p.confidence
        }
        for p in queryset
    ]

    return Response({"results": data})