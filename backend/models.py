from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class BoundingBox(BaseModel):
    class_name: str = "pothole"
    confidence: float = 0.95
    x_min: float = 0.0
    y_min: float = 0.0
    x_max: float = 1.0
    y_max: float = 1.0
    area_cm2: Optional[float] = None
    estimated_depth_cm: Optional[float] = None

class DetectionEvent(BaseModel):
    detection_id: Optional[str] = Field(default_factory=lambda: f"DET-{uuid.uuid4().hex[:6].upper()}")
    bus_id: str = Field(..., example="BUS-07")
    camera_id: Optional[str] = "CAM-BUS-07"
    event_type: str = Field("road_defect", example="road_defect") # road_defect, traffic, pedestrian_hazard
    class_name: str = Field(..., example="pothole") # pothole, road damage, waterlogging, traffic, pedestrian
    confidence: float = Field(..., example=0.94)
    latitude: float = Field(..., example=22.5512)
    longitude: float = Field(..., example=88.3524)
    timestamp: Optional[str] = None
    frame_number: Optional[int] = 1
    bounding_box: Optional[Dict[str, Any]] = None
    bounding_boxes: Optional[List[BoundingBox]] = []
    evidence_image_base64: Optional[str] = None
    evidence_image_url: Optional[str] = None
    model_version: str = Field("lunaris-yolo-v1", example="lunaris-yolo-v1")
    device_id: Optional[str] = "EDGE-JETSON-07"
    processing_latency_ms: Optional[float] = 32.5
    source_mode: str = Field("LIVE", example="LIVE") # LIVE or DEMO
    location_name: Optional[str] = "Park Street, Kolkata"
    details: Optional[str] = None

class IncidentObservation(BaseModel):
    observation_id: str = Field(default_factory=lambda: f"OBS-{uuid.uuid4().hex[:6].upper()}")
    incident_id: str
    bus_id: str
    detection_id: Optional[str] = None
    latitude: float
    longitude: float
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float
    evidence_url: Optional[str] = None
    source_mode: str = "LIVE"

class BusTelemetry(BaseModel):
    bus_id: str = Field(..., example="BUS-07")
    plate: str = Field("WB-04-E-2910", example="WB-04-E-2910")
    route_id: Optional[str] = "ROUTE-45"
    route: str = Field("Park Street → Esplanade", example="Park Street → Esplanade")
    camera_status: str = Field("Online", example="Online")
    gps_status: str = Field("Active", example="Active")
    network_status: str = Field("Online", example="Online")
    ai_status: str = Field("Active", example="Active")
    latitude: float = Field(..., example=22.5512)
    longitude: float = Field(..., example=88.3524)
    speed: float = Field(34.2, example=34.2)
    heading: Optional[float] = 85.0
    fps: float = Field(10.0, example=10.0)
    last_location: str = Field("Park Street", example="Park Street")
    timestamp: Optional[str] = None
    source_mode: str = "LIVE"

class WorkOrderCreate(BaseModel):
    incident_id: str
    department: str = "Road Maintenance Department"
    assigned_team: str = "KMC Rapid Squad 01"
    priority: str = "HIGH"
    notes: Optional[str] = None
    assigned_by: Optional[str] = "Municipal Authority HQ"

class WorkOrderUpdate(BaseModel):
    status: str # ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED
    repair_notes: Optional[str] = None
    before_evidence: Optional[str] = None
    after_evidence: Optional[str] = None
    materials_used: Optional[str] = None
    completed_by: Optional[str] = None

class ReScanVerifyEvent(BaseModel):
    incident_id: str
    bus_id: str
    latitude: float
    longitude: float
    defect_detected: bool # False = repaired/cleared; True = defect persists
    confidence: float = 0.95
    evidence_frame_url: Optional[str] = None
    timestamp: Optional[str] = None

class TrafficEventIngest(BaseModel):
    bus_id: str
    location: str
    latitude: float
    longitude: float
    vehicle_count: int = 15
    cars_count: int = 8
    buses_count: int = 2
    trucks_count: int = 1
    motorcycles_count: int = 4
    pedestrians_count: int = 6
    traffic_density: str = "HIGH" # LOW, MEDIUM, HIGH, SEVERE
    estimated_congestion_level: int = 75 # 0-100%
    average_speed_kmh: float = 18.5
    source_mode: str = "LIVE"

class PedestrianRiskIngest(BaseModel):
    bus_id: str
    location: str
    latitude: float
    longitude: float
    pedestrian_count: int = 4
    vehicle_proximity_meters: float = 2.4
    risk_score: float = 0.72 # 0.0 - 1.0 heuristic
    hazard_level: str = "MEDIUM" # LOW, MEDIUM, HIGH, CRITICAL
    reason: str = "Pedestrian crossing near accelerating vehicle"
    source_mode: str = "LIVE"

class CitizenComplaintCreate(BaseModel):
    title: str
    category: str = "Pothole"
    description: Optional[str] = None
    location: str
    latitude: float
    longitude: float
    evidence_url: Optional[str] = None
    citizen_contact: Optional[str] = None
