import cv2
import requests
import os

HF_OCR_URL = "https://vishwaridha-alpr-ml-service.hf.space/recognize/"

def recognize_plate(image_path, x1, y1, x2, y2):

    img = cv2.imread(image_path)
    if img is None:
        return {"error": "Source Not Found"}

    h, w, _ = img.shape

    x1 = max(0, int(x1))
    y1 = max(0, int(y1))
    x2 = min(w, int(x2))
    y2 = min(h, int(y2))

    crop = img[y1:y2, x1:x2]

    if crop.size == 0:
        return {"error": "Invalid Target"}

    # Improve OCR quality
    crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    temp_path = "temp_crop.jpg"
    cv2.imwrite(temp_path, crop)

    try:

        with open(temp_path, "rb") as f:
            response = requests.post(HF_OCR_URL, files={"file": f})

        os.remove(temp_path)

        print("HF STATUS:", response.status_code)
        print("HF RESPONSE:", response.text)

        if response.status_code != 200:
            return {"error": response.text}

        result = response.json()

        plate = result.get("plate_number", "")
        conf = result.get("confidence", 0)

        # Filter garbage OCR like "95"
        if len(plate) < 5:
            return {"error": "IMAGE TOO BLURRY"}

        return {
            "plate_number": plate,
            "confidence": conf
        }

    except Exception as e:
        return {"error": str(e)}