"""
LUNARIS - Quick Demo Script
Runs the trained pothole detector on a folder of images and prints clean results.
Also saves annotated copies (with bounding boxes drawn) into a 'demo_output' folder,
so you can show real before/after images during your SIH presentation without
depending on the live video stream.

Usage:
    python run_demo.py                          -> uses real_pothole_dataset/valid/images
    python run_demo.py "C:\\path\\to\\your\\photos"  -> uses your own folder
"""

import sys
import cv2
from pathlib import Path
from yolo_detector import LunarisYOLODetector

BASE_DIR = Path(__file__).parent.resolve()


def run_demo(image_folder: Path):
    print("=" * 70)
    print("       LUNARIS POTHOLE DETECTION - QUICK DEMO")
    print("=" * 70)

    detector = LunarisYOLODetector(confidence_threshold=LunarisYOLODetector.DEFAULT_CONFIDENCE_THRESHOLD)
    print(f"[*] Model: {detector.model_name}")
    print(f"[*] Weights: {detector.resolved_model_path}")
    print(f"[*] Confidence threshold: {detector.confidence_threshold}")
    print("-" * 70)

    if not image_folder.exists():
        print(f"[ERROR] Folder not found: {image_folder}")
        return

    images = sorted(list(image_folder.glob("*.jpg")) + list(image_folder.glob("*.png")) + list(image_folder.glob("*.jpeg")))
    if not images:
        print(f"[ERROR] No images found in: {image_folder}")
        return

    output_dir = BASE_DIR / "demo_output"
    output_dir.mkdir(exist_ok=True)

    total_potholes_found = 0

    for img_path in images:
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        detections, annotated = detector.detect_frame(img, debug=False)
        pothole_dets = [d for d in detections if d["class_name"] == "pothole"]

        if pothole_dets:
            total_potholes_found += 1
            best = max(pothole_dets, key=lambda d: d["confidence"])
            print(f"[POTHOLE FOUND] {img_path.name}"
                  f" -> confidence={best['confidence']}%, severity={best['severity']}, "
                  f"depth={best['estimated_depth_cm']}cm")
        else:
            print(f"[clean]         {img_path.name} -> no pothole detected")

        out_path = output_dir / f"annotated_{img_path.name}"
        cv2.imwrite(str(out_path), annotated)

    print("-" * 70)
    print(f"[+] Processed {len(images)} images. Potholes found in {total_potholes_found} images.")
    print(f"[+] Annotated images saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        folder = BASE_DIR / "real_pothole_dataset" / "valid" / "images"

    run_demo(folder)