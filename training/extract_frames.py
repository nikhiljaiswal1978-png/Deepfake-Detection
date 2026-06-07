import cv2
import os
import numpy as np
from tqdm import tqdm
import gc  
# ─────────────────────────────────────────────
# CONFIG — Edit these paths before running
# ─────────────────────────────────────────────

FAKE_VIDEOS_DIR = r"D:\FaceForensics\manipulated_sequences\Deepfakes\c40\videos"
REAL_VIDEOS_DIR = r"D:\FaceForensics\original_sequences\youtube\c40\videos"
OUTPUT_DIR      = r"D:\FaceForensics\frames"

FRAMES_PER_VIDEO = 20       # frames to extract per video
FACE_SIZE        = (224, 224)  # resize cropped face to this
FACE_PADDING     = 0.3      # extra padding around detected face (30%)
JPEG_QUALITY     = 90       # JPEG save quality (0-100)
SKIP_EXISTING    = True     # skip already-extracted videos (safe to re-run)

# ─────────────────────────────────────────────
# Load OpenCV's built-in face detector
# (no extra downloads needed)
# ─────────────────────────────────────────────

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

if face_cascade.empty():
    raise RuntimeError(
        "Could not load Haar cascade. "
        "Make sure opencv-python is installed correctly."
    )


def detect_face(frame):
    """
    Detect the largest face in a frame.
    Returns cropped + padded face as 224x224, or None if no face found.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)  # ignore tiny detections
    )

    if len(faces) == 0:
        return None

    # Pick the largest face
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

    # Add padding around face
    pad_w = int(w * FACE_PADDING)
    pad_h = int(h * FACE_PADDING)

    H, W = frame.shape[:2]
    x1 = max(0, x - pad_w)
    y1 = max(0, y - pad_h)
    x2 = min(W, x + w + pad_w)
    y2 = min(H, y + h + pad_h)

    face_crop = frame[y1:y2, x1:x2]

    if face_crop.size == 0:
        return None

    return cv2.resize(face_crop, FACE_SIZE)


def extract_frames(video_path, output_folder, video_name):
    """
    Extract FRAMES_PER_VIDEO evenly spaced frames from a video,
    crop faces, and save as JPEGs.
    Returns count of frames successfully saved.
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"  [WARN] Could not open: {video_path}")
        return 0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames == 0:
        cap.release()
        return 0

    # Pick evenly spaced frame indices 
    frame_indices = np.linspace(0, total_frames - 1, FRAMES_PER_VIDEO, dtype=int)

    saved = 0
    for i, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()

        if not ret:
            continue

        face = detect_face(frame)

        if face is None:
            # No face detected — skip this frame
            continue

        filename = f"{video_name}_f{i:02d}.jpg"
        out_path = os.path.join(output_folder, filename)
        cv2.imwrite(out_path, face, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        saved += 1

        # Free frame memory immediately 
        del frame, face

    cap.release()
    gc.collect()  # force garbage collection after each video

    return saved


def process_dataset(videos_dir, label, output_base):
    """
    Process all videos in a directory and save frames under output_base/label/
    """
    output_folder = os.path.join(output_base, label)
    os.makedirs(output_folder, exist_ok=True)

    video_files = [
        f for f in os.listdir(videos_dir)
        if f.endswith(".mp4")
    ]

    if not video_files:
        print(f"[ERROR] No .mp4 files found in: {videos_dir}")
        return

    print(f"\n{'='*50}")
    print(f"Processing: {label.upper()} ({len(video_files)} videos)")
    print(f"Output:     {output_folder}")
    print(f"{'='*50}")

    total_saved = 0
    skipped     = 0
    no_face     = 0

    for video_file in tqdm(video_files, desc=label):
        video_name = os.path.splitext(video_file)[0]

        # Skip if already extracted (safe to re-run after interruption)
        if SKIP_EXISTING:
            existing = [
                f for f in os.listdir(output_folder)
                if f.startswith(video_name + "_f")
            ]
            if len(existing) >= FRAMES_PER_VIDEO // 2:
                skipped += 1
                continue

        video_path = os.path.join(videos_dir, video_file)
        saved = extract_frames(video_path, output_folder, video_name)

        if saved == 0:
            no_face += 1
        total_saved += saved

    print(f"\n  Done.")
    print(f"  Frames saved : {total_saved}")
    print(f"  Videos skipped (already done): {skipped}")
    print(f"  Videos with no face detected : {no_face}")

    return total_saved


def main():
    print("\nFF++ Frame Extraction with Face Cropping")
    print("=========================================")
    print(f"Fake videos : {FAKE_VIDEOS_DIR}")
    print(f"Real videos : {REAL_VIDEOS_DIR}")
    print(f"Output      : {OUTPUT_DIR}")
    print(f"Frames/video: {FRAMES_PER_VIDEO}")
    print(f"Face size   : {FACE_SIZE[0]}x{FACE_SIZE[1]}")

    # Validate input paths
    for path, name in [(FAKE_VIDEOS_DIR, "Fake"), (REAL_VIDEOS_DIR, "Real")]:
        if not os.path.exists(path):
            print(f"\n[ERROR] {name} videos directory not found: {path}")
            print("Make sure the FF++ download is complete before running this script.")
            return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Process fake videos
    fake_count = process_dataset(FAKE_VIDEOS_DIR, "fake", OUTPUT_DIR)

    # Process real videos
    real_count = process_dataset(REAL_VIDEOS_DIR, "real", OUTPUT_DIR)

    # Final summary
    print(f"\n{'='*50}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*50}")
    print(f"Fake frames : {fake_count}")
    print(f"Real frames : {real_count}")
    print(f"\nOutput folder: {OUTPUT_DIR}")
    print("\nNext step: Upload the 'frames' folder to Google Drive")
    print("  fake/ -> label 0")
    print("  real/ -> label 1")


if __name__ == "__main__":
    main()
