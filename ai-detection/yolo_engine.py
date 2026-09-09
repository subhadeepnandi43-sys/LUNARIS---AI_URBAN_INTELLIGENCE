"""
LUNARIS — Edge YOLO Engine
Wraps LunarisYOLODetector for edge streams and frame analysis.
"""

import logging
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from yolo_detector import LunarisYOLODetector

logger = logging.getLogger("lunaris.yolo_engine")

# Base directory of this file (ai-detection/), used to build the default weights path relatively
BASE_DIR = Path(__file__).parent.resolve()


class RoadYOLODetector:
    """
    Unified Road YOLO Detector for Edge Streams.
    Powered strictly by custom-trained LUNEX-POTHOLE-V1 weights.
    """
    def __init__(self, model_weights: str = None, confidence_threshold: float = 0.65):
        self.conf_threshold = confidence_threshold
        resolved_weights = model_weights or str(BASE_DIR / "best.pt")
        self.detector = LunarisYOLODetector(model_path=resolved_weights, confidence_threshold=confidence_threshold)
        self.model = self.detector.model

    def process_frame(self, frame: np.ndarray, debug: bool = False) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Process a single video frame, run inference, annotate bounding boxes, and return detections.
        """
        return self.detector.detect_frame(frame, debug=debug)