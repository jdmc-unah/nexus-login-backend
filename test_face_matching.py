import os
import urllib.request
import json
import base64
import subprocess

LENA_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
OBAMA_URL = "https://upload.wikimedia.org/wikipedia/commons/8/8d/President_Barack_Obama.jpg"

LENA_PATH = "lena.jpg"
OBAMA_PATH = "obama.jpg"

def download_file(url, dest_path):
    if not os.path.exists(dest_path):
        print(f"Descargando {url} -> {dest_path}...")
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
            out_file.write(response.read())
        print("Descarga completada.")

def to_base64_data_url(filepath):
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/jpeg;base64,{data}"

def run_verifier(img1_str, img2_str):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_verifier.py")
    input_data = json.dumps({"img1": img1_str, "img2": img2_str})
    
    process = subprocess.Popen(
        ["python", script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    stdout, stderr = process.communicate(input=input_data)
    if process.returncode != 0:
        raise Exception(f"Error {process.returncode}: {stderr}")
    return json.loads(stdout.strip())

def main():
    download_file(LENA_URL, LENA_PATH)
    download_file(OBAMA_URL, OBAMA_PATH)

    print("Codificando imágenes a Base64...")
    lena_b64 = to_base64_data_url(LENA_PATH)
    obama_b64 = to_base64_data_url(OBAMA_PATH)

    print("\n--- CASO 1: Comparar Lena con ella misma (Misma Persona) ---")
    res1 = run_verifier(lena_b64, lena_b64)
    print(json.dumps(res1, indent=2))
    assert res1["verified"] == True, "Error: Deberían coincidir"
    print("¡Coincidencia correcta!")

    print("\n--- CASO 2: Comparar Lena con Barack Obama (Diferentes Personas) ---")
    res2 = run_verifier(lena_b64, obama_b64)
    print(json.dumps(res2, indent=2))
    assert res2["verified"] == False, "Error: No deberían coincidir"
    print("¡Rechazo correcto!")

    print("\n--- CASO 3: Comparar Lena con imagen vacía/sin rostro (Error esperado) ---")
    # A tiny black image
    empty_b64 = "data:image/jpeg;base64," + base64.b64encode(b'\x00'*1000).decode("utf-8")
    res3 = run_verifier(lena_b64, empty_b64)
    print(json.dumps(res3, indent=2))
    assert "error" in res3, "Error: Debería reportar un error"
    print("¡Manejo de error de rostro no detectado correcto!")

    print("\n¡Todas las pruebas automáticas biométricas pasaron con éxito!")

if __name__ == "__main__":
    main()
