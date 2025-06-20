"""
idée -->


faire un modèle dummy (la fonction qui prend les valeurs en entrée et qui lance une fonction qui renvoie une valeur)

ne pas la finir mais juste la faire fonctionner

comment elle marche  :

il doit avoir en actif autant de docker que de rtsp://<ip>:<port>/... de la caméra

il va lire en live les flux rtsp des caméras
et pour chaque flux il va faire une détection d'accident
quand un accident est détecté il va envoyer la video -30sc avant l'accident au modele gravity_data_labelisation
AVEC les metadonnées si elles sont disponibles (conditions météo, localisation, etc.)

http://www.insecam.org/en/view/800182/#camstream


<img id="image0" src="http://82.64.88.141:81/cgi-bin/camera?resolution=640&amp;amp;quality=1&amp;amp;Language=0&amp;amp;1750344626" class="img-responsive img-rounded detailimage" alt="" title="Click here to enter the camera located in France, region Ile-De-France, Paris">

// every second it will take a picture of the camera and save it in a folder with the timestamp in the name
--> 
take a picture of the camera every second and save it in a folder with the timestamp in the name
and delete the pictures older than 30 seconds
in the sub folder of temp/



OK ca march pour le côté basic ce qu'il manque :
- connection fastapi
- function plus dumy dans le quel on check si il y a un accident
- data settings pris quand on build le container
"""

import os
import time
import requests
import cv2
from datetime import datetime

# --- Settings ---
CAM_URL = "http://82.64.88.141:81/cgi-bin/camera?resolution=640&quality=1&Language=0"
IMG_SAVE_DIR = "temp/cam"
VIDEO_SAVE_DIR = "temp/video"
INTERVAL = 1  # seconds between frames
EXPIRATION_SECONDS = 60
VIDEO_INTERVAL = 30  # create video every 30 seconds
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 1  # since we're taking one frame per second


# Ensure directories exist
os.makedirs(IMG_SAVE_DIR, exist_ok=True)
os.makedirs(VIDEO_SAVE_DIR, exist_ok=True)


def cleanup_old_images():
    now = time.time()
    for fname in os.listdir(IMG_SAVE_DIR):
        fpath = os.path.join(IMG_SAVE_DIR, fname)
        if os.path.isfile(fpath):
            if now - os.path.getmtime(fpath) > EXPIRATION_SECONDS:
                os.remove(fpath)


def fetch_and_save_image():
    try:
        response = requests.get(CAM_URL, timeout=5)
        if response.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(IMG_SAVE_DIR, f"{timestamp}.jpg")
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath
    except Exception:
        pass
    return None


def get_recent_images(n_seconds=VIDEO_INTERVAL):
    now = time.time()
    files = []
    for fname in sorted(os.listdir(IMG_SAVE_DIR)):
        fpath = os.path.join(IMG_SAVE_DIR, fname)
        if os.path.isfile(fpath) and fname.endswith(".jpg"):
            if now - os.path.getmtime(fpath) <= n_seconds:
                files.append(fpath)
    return files


def create_video_from_images(image_paths, video_path):
    if not image_paths:
        return False
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, FPS, (FRAME_WIDTH, FRAME_HEIGHT))
    for img_path in image_paths:
        img = cv2.imread(img_path)
        if img is not None:
            img_resized = cv2.resize(img, (FRAME_WIDTH, FRAME_HEIGHT))
            out.write(img_resized)
    out.release()
    return True


def accident_detection_model(video_path):
    # Dummy function to simulate prediction
    print(f"Analyzing video: {video_path}")
    # Simule une détection aléatoire d'accident (une fois sur deux)
    if int(datetime.now().second) % 2 == 0:
        return "Accident Detected"
    return "No Accident"


def send_video_to_gravity_model(video_path):
    return "hi"
# --- Main Loop ---
print("Starting capture and detection loop...")
start_time = time.time()

if __name__ == "__main__":
    last_video_time = time.time()

    while True:
        filepath = fetch_and_save_image()
        cleanup_old_images()

        now = time.time()
        if now - last_video_time >= VIDEO_INTERVAL:
            image_paths = get_recent_images()
            video_name = datetime.now().strftime("accident_%Y%m%d_%H%M%S.mp4")
            video_path = os.path.join(VIDEO_SAVE_DIR, video_name)
            success = create_video_from_images(image_paths, video_path)

            if success:
                result = accident_detection_model(video_path)
                print(f"Result: {result}")

                if result == "Accident Detected":
                    # Ici, on simulerait l'envoi vers le modèle `gravity_data_labelisation`
                    print(f"Send {video_path} + metadata to gravity_data_labelisation")
            last_video_time = now

        time.sleep(INTERVAL)


