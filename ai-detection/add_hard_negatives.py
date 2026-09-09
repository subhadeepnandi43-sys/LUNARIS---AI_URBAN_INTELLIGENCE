"""
LUNARIS - Hard Negative Augmentation
Generates synthetic non-pothole road images (shadows, manholes, cracks, wet patches,
speed breakers, plain roads, and screenshot-like busy/noisy patterns) and adds them
into real_pothole_dataset/train and /valid with empty label files, so the model
learns to reject things that are NOT potholes.
"""

import random
import cv2
import numpy as np
from pathlib import Path

random.seed(7)
np.random.seed(7)

BASE_DIR = Path(__file__).parent.resolve()
DATASET_ROOT = BASE_DIR / "real_pothole_dataset"
IMG_SIZE = (640, 640)


def create_base_road_canvas():
    base_color = random.randint(35, 65)
    canvas = np.full((IMG_SIZE[1], IMG_SIZE[0], 3), base_color, dtype=np.uint8)
    noise = np.random.normal(0, random.uniform(8, 18), (IMG_SIZE[1], IMG_SIZE[0], 3)).astype(np.int16)
    canvas = np.clip(canvas.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return canvas


def generate_negative_sample(neg_type):
    canvas = create_base_road_canvas()

    if neg_type == "normal_road":
        pass
    elif neg_type == "shadow":
        overlay = canvas.copy()
        poly = np.array([[0, random.randint(100, 300)], [IMG_SIZE[0], random.randint(300, 500)],
                          [IMG_SIZE[0], IMG_SIZE[1]], [0, IMG_SIZE[1]]], dtype=np.int32)
        cv2.fillPoly(overlay, [poly], (12, 12, 16))
        cv2.addWeighted(overlay, 0.65, canvas, 0.35, 0, canvas)
    elif neg_type == "crack":
        curr_x, curr_y = random.randint(100, IMG_SIZE[0] - 100), random.randint(50, 200)
        for _ in range(random.randint(15, 30)):
            next_x = curr_x + random.randint(-18, 18)
            next_y = curr_y + random.randint(12, 28)
            cv2.line(canvas, (curr_x, curr_y), (next_x, next_y), (20, 20, 20), thickness=random.randint(1, 3))
            curr_x, curr_y = next_x, next_y
    elif neg_type == "manhole":
        mx, my = random.randint(150, IMG_SIZE[0] - 150), random.randint(200, IMG_SIZE[1] - 150)
        radius = random.randint(50, 95)
        cv2.circle(canvas, (mx, my), radius, (55, 55, 58), -1)
        cv2.circle(canvas, (mx, my), radius, (75, 75, 80), 3)
    elif neg_type == "water_reflection":
        wx, wy = random.randint(150, IMG_SIZE[0] - 150), random.randint(200, IMG_SIZE[1] - 150)
        overlay = canvas.copy()
        cv2.ellipse(overlay, (wx, wy), (random.randint(80, 180), random.randint(40, 90)),
                     random.randint(0, 30), 0, 360, (140, 160, 180), -1)
        cv2.addWeighted(overlay, 0.4, canvas, 0.6, 0, canvas)
    elif neg_type == "speed_breaker":
        by, bh = random.randint(250, IMG_SIZE[1] - 200), random.randint(50, 90)
        cv2.rectangle(canvas, (0, by), (IMG_SIZE[0], by + bh), (45, 45, 50), -1)
        for x_pos in range(0, IMG_SIZE[0], 60):
            pts = np.array([[x_pos, by], [x_pos + 30, by], [x_pos + 50, by + bh], [x_pos + 20, by + bh]], dtype=np.int32)
            cv2.fillPoly(canvas, [pts], (0, 215, 255))
    elif neg_type == "busy_ui_noise":
        # Screenshot/UI-like noisy pattern (blocky colored regions) - targets the
        # false-positive weakness found when testing with a code-editor screenshot.
        for _ in range(random.randint(20, 40)):
            x, y = random.randint(0, IMG_SIZE[0] - 60), random.randint(0, IMG_SIZE[1] - 30)
            w, h = random.randint(20, 120), random.randint(10, 40)
            color = tuple(int(c) for c in np.random.randint(0, 255, 3))
            cv2.rectangle(canvas, (x, y), (x + w, y + h), color, -1)
    elif neg_type == "stone":
        for _ in range(random.randint(6, 18)):
            sx, sy = random.randint(100, IMG_SIZE[0] - 100), random.randint(150, IMG_SIZE[1] - 100)
            scolor = random.randint(150, 210)
            cv2.circle(canvas, (sx, sy), random.randint(3, 8), (scolor, scolor, scolor), -1)

    return canvas


def add_negatives():
    print("[+] Generating hard-negative (non-pothole) images...")

    neg_types = ["normal_road", "shadow", "crack", "manhole",
                 "water_reflection", "speed_breaker", "busy_ui_noise", "stone"]

    for split, count_per_type in [("train", 15), ("valid", 4)]:
        img_dir = DATASET_ROOT / split / "images"
        lbl_dir = DATASET_ROOT / split / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        added = 0
        for neg_type in neg_types:
            for i in range(count_per_type):
                img = generate_negative_sample(neg_type)
                filename = f"neg_{neg_type}_{i:03d}"
                cv2.imwrite(str(img_dir / f"{filename}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
                # Empty label file = "no pothole here"
                (lbl_dir / f"{filename}.txt").write_text("")
                added += 1

        print(f"  [OK] {split}: added {added} negative images")

    print("[+] Done. Negative images now mixed into real_pothole_dataset train/valid splits.")


if __name__ == "__main__":
    add_negatives()          