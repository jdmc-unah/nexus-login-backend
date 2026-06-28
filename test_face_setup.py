import os
import urllib.request
import cv2

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

YUNET_PATH = os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "face_recognition_sface_2021dec.onnx")

def download_file(url, dest_path):
    print(f"Descargando {url} -> {dest_path}...")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    # Simple downloader
    urllib.request.urlretrieve(url, dest_path)
    print("Descarga completada.")

def main():
    if not os.path.exists(YUNET_PATH):
        download_file(YUNET_URL, YUNET_PATH)
    else:
        print("YuNet model ya existe.")

    if not os.path.exists(SFACE_PATH):
        download_file(SFACE_URL, SFACE_PATH)
    else:
        print("SFace model ya existe.")

    print("Cargando YuNet...")
    # Initialize YuNet detector with dummy input size
    detector = cv2.FaceDetectorYN.create(YUNET_PATH, "", (320, 320))
    print("YuNet detector inicializado correctamente.")

    print("Cargando SFace...")
    recognizer = cv2.FaceRecognizerSF.create(SFACE_PATH, "")
    print("SFace recognizer inicializado correctamente.")

    print("¡Configuración de modelos de rostros completada con éxito!")

if __name__ == "__main__":
    main()
