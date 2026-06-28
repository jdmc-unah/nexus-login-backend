import sys
import json
import base64
import numpy as np
import cv2
import os

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
YUNET_PATH = os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "face_recognition_sface_2021dec.onnx")

def decode_base64_image(base64_str):
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    img_bytes = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def resize_if_large(img, max_dim=640):
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h))
    return img

def main():
    # Set encoding to utf-8 to avoid Windows console character errors
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    try:
        input_data = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"verified": False, "error": f"Error al parsear input JSON: {str(e)}"}))
        return

    img1_str = input_data.get("img1")
    img2_str = input_data.get("img2")

    if not img1_str or not img2_str:
        print(json.dumps({"verified": False, "error": "Se requieren las dos imágenes img1 e img2."}))
        return

    try:
        img1 = decode_base64_image(img1_str)
        img2 = decode_base64_image(img2_str)
    except Exception as e:
        print(json.dumps({"verified": False, "error": f"Error al decodificar imágenes: {str(e)}"}))
        return

    if img1 is None or img2 is None:
        print(json.dumps({"verified": False, "error": "Una de las imágenes no se pudo cargar correctamente (formato inválido)."}))
        return

    # Resize to standardized dimensions for faster and more accurate YuNet inference
    img1 = resize_if_large(img1)
    img2 = resize_if_large(img2)

    # Check models exist
    if not os.path.exists(YUNET_PATH) or not os.path.exists(SFACE_PATH):
        print(json.dumps({"verified": False, "error": "Los modelos de detección/reconocimiento facial no están instalados."}))
        return

    try:
        # Detect faces in img1
        h1, w1 = img1.shape[:2]
        detector1 = cv2.FaceDetectorYN.create(YUNET_PATH, "", (w1, h1))
        _, faces1 = detector1.detect(img1)

        # Detect faces in img2
        h2, w2 = img2.shape[:2]
        detector2 = cv2.FaceDetectorYN.create(YUNET_PATH, "", (w2, h2))
        _, faces2 = detector2.detect(img2)

        if faces1 is None or len(faces1) == 0:
            print(json.dumps({"verified": False, "error": "No se detectó rostro en la firma facial registrada."}))
            return

        if faces2 is None or len(faces2) == 0:
            print(json.dumps({"verified": False, "error": "No se detectó rostro en la captura actual de la cámara."}))
            return

        # Align and extract features
        recognizer = cv2.FaceRecognizerSF.create(SFACE_PATH, "")
        
        face1_align = recognizer.alignCrop(img1, faces1[0])
        face2_align = recognizer.alignCrop(img2, faces2[0])

        feat1 = recognizer.feature(face1_align)
        feat2 = recognizer.feature(face2_align)

        # Cosine similarity matching (higher is closer/more similar)
        similarity = float(recognizer.match(feat1, feat2, cv2.FaceRecognizerSF_FR_COSINE))

        # SFace cosine similarity threshold is typically 0.363 (values higher mean same identity)
        THRESHOLD = 0.363
        verified = similarity >= THRESHOLD

        print(json.dumps({
            "verified": verified,
            "score": similarity,
            "threshold": THRESHOLD,
            "metric": "cosine_similarity"
        }))

    except Exception as e:
        print(json.dumps({"verified": False, "error": f"Error durante el procesamiento biométrico: {str(e)}"}))

if __name__ == "__main__":
    main()
