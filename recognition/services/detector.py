from ultralytics import YOLO
import os
import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "best.pt")

model = YOLO(MODEL_PATH)

def enhance_for_ocr(img_crop):
    """
    Enhances the cropped license plate to fix blur issues.
    """
    if img_crop is None or img_crop.size == 0:
        return img_crop
        
    # 1. Upscale the crop to give OCR more pixels to work with
    img_crop = cv2.resize(img_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # 2. Convert to Grayscale
    gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
    
    # 3. Apply Sharpening Kernel
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    
    # 4. Adaptive Thresholding to make text pop
    enhanced = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    return enhanced

def detect_plates(image_path):
    # Higher confidence (0.50) ensures we only show boxes likely to be readable
    results = model(image_path, conf=0.50,imgsz=960)
    
    current_boxes = []
    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])

        current_boxes.append({
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "confidence": round(conf * 100, 2)
        })

    # FIX: Only return the top 1 detection if you only want to see one image detected
    # Or return the full list if you want to see all current frame detections.
    # We do NOT use global memory here to avoid the "Ghost Box" mess.
    return sorted(current_boxes, key=lambda x: x["confidence"], reverse=True)

def get_enhanced_crop(image_path, x1, y1, x2, y2):
    """
    Call this inside your recognize-plate view before passing to OCR
    """
    img = cv2.imread(image_path)
    crop = img[y1:y2, x1:x2]
    return enhance_for_ocr(crop)