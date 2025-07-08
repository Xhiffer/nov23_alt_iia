import os
import time
import requests
import cv2
from datetime import datetime
import subprocess

# --- Settings ---
CAM_URL = "http://92.85.14.184:83/onvif/snapshot/1/11"  # IP camera snapshot URL
IMG_SAVE_DIR = "temp/cam"
VIDEO_SAVE_DIR = "temp/video"
INTERVAL = 1  # seconds between each image capture
EXPIRATION_SECONDS = 60  # delete images older than this
VIDEO_INTERVAL = 30  # interval to create a new video (in seconds)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 1  # 1 frame per second

# Ensure save directories exist
os.makedirs(IMG_SAVE_DIR, exist_ok=True)
os.makedirs(VIDEO_SAVE_DIR, exist_ok=True)


def cleanup_old_images():
    """Delete old images from the image folder."""
    now = time.time()
    for fname in os.listdir(IMG_SAVE_DIR):
        fpath = os.path.join(IMG_SAVE_DIR, fname)
        if os.path.isfile(fpath):
            if now - os.path.getmtime(fpath) > EXPIRATION_SECONDS:
                os.remove(fpath)


def fetch_and_save_image():
    """Fetch image from camera and save it with timestamp."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(CAM_URL, timeout=5, headers=headers)
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
    """Get image paths from the last N seconds."""
    now = time.time()
    files = []
    for fname in sorted(os.listdir(IMG_SAVE_DIR)):
        fpath = os.path.join(IMG_SAVE_DIR, fname)
        if os.path.isfile(fpath) and fname.endswith(".jpg"):
            if now - os.path.getmtime(fpath) <= n_seconds:
                files.append(fpath)
    return files


def create_video_from_images(image_paths, video_path):
    """Create a video from a sequence of images."""
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


def fix_video_metadata(input_path, output_path):
    """Re-encode video using ffmpeg for browser compatibility."""
    command = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        output_path,
        "-y"  # overwrite output file
    ]
    subprocess.run(command, check=True)


def accident_detection_model(video_path):
    """Simulated accident detection model."""
    print(f"Analyzing video: {video_path}")
    # Dummy logic for testing
    # if int(datetime.now().second) % 2 == 0:
    if True :
        return "Accident Detected"
    return "No Accident"


def send_video_to_accident_data_labelisation_model(video_path: str):
    """Send video to external service for labeling and estimation."""
    url = "http://ai_model_accident_labelisation:82/labelise_and_estime/"
    try:
        with open(video_path, "rb") as video_file:
            files = {"video": video_file}
            response = requests.post(url, files=files)
            response.raise_for_status()
            print(response.json())
    except Exception as e:
        print(f"Error sending video: {e}")
        return None

    try:
        os.remove(video_path)
        print(f"Deleted video: {video_path}")
    except Exception as e:
        print(f"Error deleting video file: {e}")

    return response.json()


# --- Main Loop ---
print("Starting capture and detection loop...")

if __name__ == "__main__":
    # Initial cleanup
    for img_file in os.listdir(IMG_SAVE_DIR):
        try:
            os.remove(os.path.join(IMG_SAVE_DIR, img_file))
            print(f"Deleted {img_file}")
        except Exception as e:
            print(f"Error deleting {img_file}: {e}")

    last_video_time = time.time()

    while True:
        # Step 1: Fetch image
        filepath = fetch_and_save_image()
        cleanup_old_images()

        # Step 2: Create video periodically
        now = time.time()
        if now - last_video_time >= VIDEO_INTERVAL:
            image_paths = get_recent_images()
            video_name = datetime.now().strftime("accident_%Y%m%d_%H%M%S.mp4")
            video_path = os.path.join(VIDEO_SAVE_DIR, video_name)

            success = create_video_from_images(image_paths, video_path)
            if success:
                # Re-encode video for browser compatibility
                fixed_video_path = video_path.replace(".mp4", "_fixed.mp4")
                try:
                    fix_video_metadata(video_path, fixed_video_path)
                except Exception as e:
                    print(f"FFmpeg re-encoding failed: {e}")
                    fixed_video_path = video_path  # fallback

                # Simulate accident detection
                result = accident_detection_model(fixed_video_path)
                print(f"Result: {result}")

                if result == "Accident Detected":
                    print(f"Send {fixed_video_path} to accident_data_labelisation")
                    send_video_to_accident_data_labelisation_model(fixed_video_path)

                # Delete the original non-fixed video
                try:
                    os.remove(video_path)
                    print(f"Deleted original video: {video_path}")
                except Exception as e:
                    print(f"Error deleting original video file: {e}")

            last_video_time = now

        time.sleep(INTERVAL)
