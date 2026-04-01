import cv2
import os
import uuid

def extract_frames(video_path, media_root):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, []

    folder_name = uuid.uuid4().hex
    folder_path = os.path.join(media_root, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    frames = []
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % 15 == 0:
            frame_path = os.path.join(folder_path, f"frame_{count}.jpg")
            cv2.imwrite(frame_path, frame)
            frames.append(frame_path)

        count += 1

    cap.release()
    return folder_name, frames