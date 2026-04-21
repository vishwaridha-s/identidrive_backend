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
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .ocr_utils import recognize_plate
from .models import PlatePrediction
from django.views.decorators.csrf import csrf_exempt


@api_view(['POST'])
@csrf_exempt
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

@api_view(['POST'])
@csrf_exempt
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

@api_view(['POST'])
@csrf_exempt
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
            user=request.user if request.user.is_authenticated else None,
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

@api_view(['POST'])
@csrf_exempt
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

@api_view(['GET'])
def get_predictions(request):
    date = request.GET.get("date")

    if not request.user.is_authenticated:
        return Response({"results": []})

    queryset = PlatePrediction.objects.filter(user=request.user).order_by("-created_at")

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

@api_view(['POST'])
@csrf_exempt
def signup_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')

    if not username or not password:
        return Response({"error": "Username and password required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)
    user.save()
    return Response({"message": "User created successfully"})

@api_view(['POST'])
@csrf_exempt
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({"error": "Username and password required"}, status=400)

    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({"message": "Login successful", "username": user.username})
    else:
        if not User.objects.filter(username=username).exists():
            return Response({"error": "User not found. Redirecting to signup.", "redirect_signup": True}, status=404)
        return Response({"error": "Invalid credentials"}, status=401)

@api_view(['POST'])
@csrf_exempt
def logout_view(request):
    logout(request)
    return Response({"message": "Logged out successfully"})
