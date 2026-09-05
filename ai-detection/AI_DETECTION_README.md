# LUNARIS - AI Detection Module

Part of Team LUNEX's SIH26124 submission: AI-Powered Mobile Urban Intelligence
Platform Using Public Transport Fleet.

This module is the YOLOv8-based pothole detection engine. It watches a bus
camera feed (or an uploaded photo) and reports potholes with confidence,
severity, and estimated depth.

## What's in here

- `main.py` - FastAPI service (port 8001). This is the one you run.
- `yolo_detector.py` - Core detection logic (loads `best.pt`, runs inference).
- `yolo_engine.py` - Thin wrapper around the detector for edge/stream use.
- `stream_processor.py` - Handles live video streams with multi-frame
  confirmation (a pothole must appear in 3+ consecutive frames before it's
  reported, to avoid one-off false alarms).
- `train_pothole_model.py` - Fine-tunes YOLOv8n on `real_pothole_dataset/`.
- `prepare_dataset.py` - Generates synthetic pothole images (fallback/testing
  only - the real dataset in `real_pothole_dataset/` is what the model is
  actually trained on).
- `add_hard_negatives.py` - Adds synthetic non-pothole images (shadows,
  manholes, wet patches, etc.) to reduce false positives.
- `test_pothole_validation.py` - Runs the model against the validation set
  and reports recall / false-positive rate.
- `run_demo.py` - Standalone demo: runs the model on a folder of images and
  saves annotated results to `demo_output/`. Use this for a reliable demo
  that doesn't depend on a live video stream.
- `detector.py` - Older standalone edge-worker script. Not currently used by
  `main.py`; kept for reference only.

## Setup

```
pip install -r requirements.txt
```

## Running the detection API

```
python main.py
```

Then open `http://localhost:8001/docs` to test image uploads via
`/api/ai/detect`, or check `/api/ai/health` for model status.

## Running the quick demo (recommended for presentations)

```
python run_demo.py
```

Prints results for every image in `real_pothole_dataset/valid/images` and
saves annotated copies to `demo_output/`.

## Retraining the model

```
python add_hard_negatives.py   # optional: adds non-pothole examples
python train_pothole_model.py  # takes ~30-60+ min on CPU
```

## Known limitations

- Confidence threshold is set to 0.75 as a practical balance. Real potholes
  in testing scored 75-85%; some visually unusual non-road images can still
  occasionally trigger a false positive. More real-world training photos
  (not synthetic) would improve this further.
- Live RTSP streaming (`/api/ai/stream/{bus_id}`) works but can show frame
  corruption artifacts under local CPU-only testing conditions. The
  photo-upload endpoint (`/api/ai/detect`) is fully reliable and recommended
  for demos.