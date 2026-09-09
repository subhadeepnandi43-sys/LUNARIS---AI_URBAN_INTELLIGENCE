"""
LUNARIS Model Taxonomy & Classes Architecture
SIH 2026 Problem Statement: SIH26124

Defines explicit taxonomy for:
1. Road Surface Defect Detection
2. Urban Traffic Density & Vehicle Counting
3. Model Training Registry & Deployment Status
"""

from typing import Dict, Any, List

# Supported Road Surface Defects in LUNARIS Platform Architecture
ROAD_DEFECT_CLASSES: Dict[str, Dict[str, Any]] = {
    "pothole": {
        "label": "Pothole",
        "description": "Cavity or crater in asphalt surface",
        "severity_default": "HIGH",
        "trained_in_best_pt": True,  # Actively trained in custom YOLOv8 model best.pt
        "detection_confidence_threshold": 0.60
    },
    "road damage/crack": {
        "label": "Road Damage / Fissure",
        "description": "Longitudinal or alligator cracking in pavement",
        "severity_default": "MEDIUM",
        "trained_in_best_pt": False,  # Model roadmap: scheduled for V2 dataset
        "detection_confidence_threshold": 0.65
    },
    "waterlogging": {
        "label": "Waterlogging / Pooling",
        "description": "Surface water accumulation indicating drainage failure",
        "severity_default": "HIGH",
        "trained_in_best_pt": False,
        "detection_confidence_threshold": 0.70
    },
    "missing/damaged divider": {
        "label": "Damaged Median Divider",
        "description": "Displaced, damaged, or unpainted lane divider",
        "severity_default": "CRITICAL",
        "trained_in_best_pt": False,
        "detection_confidence_threshold": 0.75
    },
    "missing/damaged zebra crossing": {
        "label": "Faded Zebra Crossing",
        "description": "Pedestrian crosswalk with degraded reflectivity",
        "severity_default": "MEDIUM",
        "trained_in_best_pt": False,
        "detection_confidence_threshold": 0.70
    },
    "damaged/missing traffic sign": {
        "label": "Damaged Traffic Sign",
        "description": "Fallen, occluded, or bent regulatory signage",
        "severity_default": "HIGH",
        "trained_in_best_pt": False,
        "detection_confidence_threshold": 0.75
    },
    "road obstruction": {
        "label": "Road Obstruction",
        "description": "Debris, fallen branches, or unbarricaded road work",
        "severity_default": "CRITICAL",
        "trained_in_best_pt": False,
        "detection_confidence_threshold": 0.70
    },
    "other hazards": {
        "label": "General Hazard",
        "description": "Unclassified roadway surface or structural anomaly",
        "severity_default": "MEDIUM",
        "trained_in_best_pt": False,
        "detection_confidence_threshold": 0.65
    }
}

# Supported Vehicle & Pedestrian Classes for Traffic Intelligence
TRAFFIC_CLASSES: List[str] = [
    "car",
    "bus",
    "truck",
    "motorcycle",
    "bicycle",
    "pedestrian",
    "auto/rickshaw"
]

def calculate_congestion_level(total_vehicles: int) -> str:
    """
    Computes explainable urban traffic congestion level:
    0-3: LOW
    4-8: MEDIUM
    9-15: HIGH
    >15: SEVERE
    """
    if total_vehicles <= 3:
        return "LOW"
    elif total_vehicles <= 8:
        return "MEDIUM"
    elif total_vehicles <= 15:
        return "HIGH"
    else:
        return "SEVERE"

def get_model_capabilities() -> Dict[str, Any]:
    """Returns honest model capabilities for SIH presentation."""
    trained_defects = [k for k, v in ROAD_DEFECT_CLASSES.items() if v["trained_in_best_pt"]]
    roadmap_defects = [k for k, v in ROAD_DEFECT_CLASSES.items() if not v["trained_in_best_pt"]]
    return {
        "active_weights": "best.pt / yolov8n.pt",
        "trained_defect_classes": trained_defects,
        "taxonomy_roadmap_classes": roadmap_defects,
        "traffic_classes": TRAFFIC_CLASSES,
        "traffic_levels": ["LOW", "MEDIUM", "HIGH", "SEVERE"]
    }
