"""
LUNEX AI Pothole Detection Validation Suite
Tests LUNEX-POTHOLE-V1 against the real "valid" split of real_pothole_dataset
(images with labeled potholes vs. clean images with none).
Confirms high detection rate on real potholes and low false positives on clean images.
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path

# Add ai-detection to path
sys.path.insert(0, str(Path(__file__).parent.resolve()))
from yolo_detector import LunarisYOLODetector

# Base directory of this file (ai-detection/), used to build the dataset path relatively
BASE_DIR = Path(__file__).parent.resolve()

def run_comprehensive_validation():
    print("\n" + "="*70)
    print("      LUNEX-POTHOLE-V1 COMPREHENSIVE VALIDATION SUITE")
    print("="*70)

    detector = LunarisYOLODetector(confidence_threshold=0.65)
    print(f"[*] Detector Model: {detector.model_name}")
    print(f"[*] Resolved Path:  {detector.resolved_model_path}")
    print(f"[*] Model Loaded:   {detector.is_loaded}")
    print(f"[*] Conf Threshold: {detector.confidence_threshold}")
    print("-" * 70)

    val_img_dir = BASE_DIR / "real_pothole_dataset" / "valid" / "images"
    val_lbl_dir = BASE_DIR / "real_pothole_dataset" / "valid" / "labels"
    val_images = list(val_img_dir.glob("*.jpg")) + list(val_img_dir.glob("*.png")) + list(val_img_dir.glob("*.jpeg"))
    print(f"[*] Total Unseen Validation Images: {len(val_images)}")

    total_images = 0
    images_with_ground_truth_pothole = 0
    correctly_detected = 0
    images_with_no_ground_truth = 0
    false_positives_on_clean_images = 0

    detailed_results = []

    for img_path in val_images:
        label_path = val_lbl_dir / f"{img_path.stem}.txt"
        has_ground_truth = label_path.exists() and label_path.stat().st_size > 0

        img = cv2.imread(str(img_path))
        if img is None:
            continue

        total_images += 1
        detections, _ = detector.detect_frame(img)
        pothole_dets = [d for d in detections if d["class_name"] == "pothole"]

        if has_ground_truth:
            images_with_ground_truth_pothole += 1
            if len(pothole_dets) > 0:
                correctly_detected += 1
        else:
            images_with_no_ground_truth += 1
            if len(pothole_dets) > 0:
                false_positives_on_clean_images += 1

        detailed_results.append({
            "image": img_path.name,
            "has_ground_truth": has_ground_truth,
            "detections_count": len(pothole_dets),
            "max_conf": max([d["confidence"] for d in pothole_dets]) if pothole_dets else 0.0
        })

    print(f"\n{'='*70}")
    print(f"  Total Validation Images:          {total_images}")
    print(f"  Images WITH labeled pothole(s):    {images_with_ground_truth_pothole}")
    print(f"  Images with NO pothole (clean):     {images_with_no_ground_truth}")
    print("-" * 70)

    pos_recall = (correctly_detected / images_with_ground_truth_pothole * 100) if images_with_ground_truth_pothole > 0 else 0
    neg_specificity = (
        (images_with_no_ground_truth - false_positives_on_clean_images) / images_with_no_ground_truth * 100
    ) if images_with_no_ground_truth > 0 else 100

    print(f"  Detection Recall (found a real pothole):     {pos_recall:.1f}% ({correctly_detected}/{images_with_ground_truth_pothole})")
    print(f"  False Positive Rejection (clean images):     {neg_specificity:.1f}% ({images_with_no_ground_truth - false_positives_on_clean_images}/{images_with_no_ground_truth})")
    print("=" * 70 + "\n")

    return {
        "positive_recall": pos_recall,
        "negative_rejection": neg_specificity,
        "model_name": detector.model_name,
        "confidence_threshold": detector.confidence_threshold
    }

if __name__ == "__main__":
    run_comprehensive_validation()