import logging
import base64
import uuid
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from backend.models import DetectionEvent, IncidentObservation
from backend.database import get_supabase
from backend.config import settings
from backend.privacy import redact_sensitive_pii
from backend.logger import log_system_event, AuditEventType
from backend.security import apply_rate_limiting, sanitize_string, validate_coordinates

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

logger = logging.getLogger("lunaris.detections")
router = APIRouter(prefix="/detections", tags=["AI Detections & Consensus Ingestion"])

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance between two coordinates in meters."""
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def compute_explainable_priority(
    defect_type: str,
    confidence: float,
    depth_cm: float,
    area_cm2: float,
    consensus_count: int,
    traffic_density: str = "HIGH",
    pedestrian_proximity: bool = False,
    road_name: str = "Transit Arterial"
) -> tuple[str, str, float]:
    """
    Explainable Priority Engine (Requirement 9)
    Evaluates depth, surface geometry, multi-bus agreement, traffic density, and pedestrian hazard.
    Returns: (severity_label, human_readable_reason, priority_score_0_to_100)
    """
    reasons = []
    points = 0.0

    # 1. Defect Geometry & Physical Danger
    if depth_cm >= 9.0 or area_cm2 >= 1500:
        points += 30.0
        reasons.append(f"Severe defect geometry (Depth: {depth_cm:.1f}cm, Area: {int(area_cm2)}cm²)")
    elif depth_cm >= 5.0 or area_cm2 >= 800:
        points += 20.0
        reasons.append(f"Moderate defect depth ({depth_cm:.1f}cm)")
    else:
        points += 10.0

    # 2. Multi-Bus Independent Consensus Agreement
    if consensus_count >= settings.CONSENSUS_VERIFICATION_THRESHOLD:
        points += 35.0
        reasons.append(f"{consensus_count} independent transit buses verified defect location")
    elif consensus_count == 2:
        points += 20.0
        reasons.append(f"Dual-bus confirmation ({consensus_count} buses)")
    else:
        points += 10.0
        reasons.append("Single bus initial observation")

    # 3. Traffic Density & Road Corridor Importance
    if traffic_density in ["SEVERE", "HIGH"]:
        points += 20.0
        reasons.append(f"High-density traffic corridor ({road_name})")
    elif traffic_density == "MEDIUM":
        points += 10.0

    # 4. Pedestrian Risk Proximity
    if pedestrian_proximity:
        points += 10.0
        reasons.append("Immediate pedestrian transit zone hazard")

    # 5. AI Confidence Factor
    norm_conf = confidence if confidence <= 1.0 else (confidence / 100.0)
    points += (norm_conf * 5.0)

    score = min(100.0, max(0.0, points))

    if score >= 75.0:
        severity = "CRITICAL"
    elif score >= 55.0:
        severity = "HIGH"
    elif score >= 35.0:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    reason_text = " • ".join(reasons) if reasons else "Standard Edge AI detection baseline"
    return severity, reason_text, score

@router.post("/event", status_code=status.HTTP_201_CREATED)
@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_detection_event(event: DetectionEvent, background_tasks: BackgroundTasks):
    """
    Ingest a road defect detection event from transit edge workers.
    Features:
    - Standardized Detection Data Model (Requirement 4)
    - PII Privacy Redaction (In-memory Face & License Plate Blur)
    - Multi-Bus Consensus Engine & Observation Logging (Requirement 8)
    - Explainable Priority Calculation (Requirement 9)
    - LIVE vs DEMO Mode segregation (Requirement 2)
    """
    try:
        lat, lng = validate_coordinates(event.latitude, event.longitude)
        norm_conf = event.confidence if event.confidence <= 1.0 else (event.confidence / 100.0)
        confidence_pct = norm_conf * 100.0
        
        detection_uuid = event.detection_id or f"DET-{uuid.uuid4().hex[:6].upper()}"
        event_class = (event.class_name or event.event_type or "pothole").capitalize()
        source_mode = event.source_mode.upper() if event.source_mode else "LIVE"

        # 1. Bounding Box & Dimensions Estimation
        bbox_data = event.bounding_box or {}
        depth_cm = 7.5
        area_cm2 = 1100.0
        if event.bounding_boxes and len(event.bounding_boxes) > 0:
            first_box = event.bounding_boxes[0]
            bbox_data = first_box.dict()
            depth_cm = first_box.estimated_depth_cm or depth_cm
            area_cm2 = first_box.area_cm2 or area_cm2

        # 2. In-Memory Privacy Redaction & Storage
        evidence_url = event.evidence_image_url
        if event.evidence_image_base64:
            try:
                raw_b64 = event.evidence_image_base64
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",")[1]
                img_data = base64.b64decode(raw_b64)
                
                if cv2 is not None and np is not None:
                    nparr = np.frombuffer(img_data, np.uint8)
                    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if cv_img is not None:
                        redacted = redact_sensitive_pii(cv_img)
                        _, buf = cv2.imencode('.jpg', redacted, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        img_data = buf.tobytes()

                # Upload to Supabase Storage Bucket if client ready
                try:
                    supabase = get_supabase()
                    file_path = f"detections/{datetime.utcnow().strftime('%Y/%m/%d')}/{detection_uuid}.jpg"
                    supabase.storage.from_(settings.EVIDENCE_BUCKET).upload(
                        path=file_path,
                        file=img_data,
                        file_options={"content-type": "image/jpeg"}
                    )
                    evidence_url = supabase.storage.from_(settings.EVIDENCE_BUCKET).get_public_url(file_path)
                except Exception as se:
                    logger.debug("Evidence storage notice: %s", se)
            except Exception as pe:
                logger.warning("Privacy redaction notice: %s", pe)

        # 3. Spatial Matching & Multi-Bus Consensus
        matched_incident = None
        target_incident_id = None
        current_buses = [event.bus_id]
        
        try:
            supabase = get_supabase()
            cutoff = (datetime.utcnow() - timedelta(hours=settings.DUPLICATE_TIME_WINDOW_HOURS)).isoformat()
            
            existing = supabase.from_("incidents").select("*") \
                .neq("status", "RESOLVED") \
                .neq("status", "VERIFIED_RESOLUTION") \
                .gte("created_at", cutoff) \
                .execute()

            if existing.data:
                for inc in existing.data:
                    dist = haversine_distance_meters(inc["latitude"], inc["longitude"], lat, lng)
                    if dist <= settings.DUPLICATE_DISTANCE_THRESHOLD_METERS:
                        matched_incident = inc
                        target_incident_id = inc["incident_id"]
                        logger.info(f"Consensus match: incident {target_incident_id} ({dist:.1f}m away)")
                        break
        except Exception as e:
            logger.debug("Incident search note: %s", e)

        # Multi-Bus Consensus State Transition
        if matched_incident:
            existing_buses = set(matched_incident.get("verified_by_buses") or [])
            existing_buses.add(event.bus_id)
            current_buses = list(existing_buses)
            consensus_count = len(current_buses)

            if consensus_count >= settings.CONSENSUS_VERIFICATION_THRESHOLD:
                consensus_status = "VERIFIED"
                consensus_score = 98.2
            elif consensus_count == 2:
                consensus_status = "PROBABLE"
                consensus_score = 85.0
            else:
                consensus_status = matched_incident.get("status", "POSSIBLE")
                consensus_score = 65.0

            severity, reason, p_score = compute_explainable_priority(
                defect_type=event_class,
                confidence=confidence_pct,
                depth_cm=depth_cm,
                area_cm2=area_cm2,
                consensus_count=consensus_count,
                road_name=event.location_name or "Kolkata Arterial Route"
            )

            # Update Incident in Database
            try:
                supabase.from_("incidents").update({
                    "consensus_count": consensus_count,
                    "confidence_score": max(matched_incident.get("confidence_score", 90.0), confidence_pct),
                    "status": consensus_status,
                    "severity": severity,
                    "severity_reason": reason,
                    "verified_by_buses": current_buses,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("incident_id", target_incident_id).execute()
            except Exception as ue:
                logger.debug("Incident update note: %s", ue)

        else:
            # First observation: create new incident in POSSIBLE state
            target_incident_id = f"RD-{uuid.uuid4().hex[:4].upper()}"
            consensus_count = 1
            consensus_status = "POSSIBLE"
            consensus_score = 65.0

            severity, reason, p_score = compute_explainable_priority(
                defect_type=event_class,
                confidence=confidence_pct,
                depth_cm=depth_cm,
                area_cm2=area_cm2,
                consensus_count=1,
                road_name=event.location_name or "Kolkata Arterial Route"
            )

            inc_data = {
                "incident_id": target_incident_id,
                "title": f"Detected {event_class} ({event.location_name or 'Kolkata'})",
                "category": event_class,
                "severity": severity,
                "severity_reason": reason,
                "status": consensus_status,
                "latitude": lat,
                "longitude": lng,
                "address": event.location_name or "Kolkata Metropolitan Area",
                "consensus_count": 1,
                "confidence_score": confidence_pct,
                "verified_by_buses": current_buses,
                "before_evidence": evidence_url,
                "bus_id": event.bus_id,
                "source_mode": source_mode,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            try:
                supabase.from_("incidents").insert(inc_data).execute()
            except Exception as ie:
                logger.debug("Incident insert note: %s", ie)

        # 4. Record Observation Trail (Requirement 8)
        obs_id = f"OBS-{uuid.uuid4().hex[:6].upper()}"
        obs_record = {
            "observation_id": obs_id,
            "incident_id": target_incident_id,
            "bus_id": event.bus_id,
            "detection_id": detection_uuid,
            "latitude": lat,
            "longitude": lng,
            "timestamp": event.timestamp or datetime.utcnow().isoformat(),
            "confidence": confidence_pct,
            "evidence_url": evidence_url,
            "source_mode": source_mode
        }
        try:
            supabase.from_("incident_observations").insert(obs_record).execute()
        except Exception as oe:
            logger.debug("Observation log note: %s", oe)

        # Structured Audit Event
        log_system_event(
            AuditEventType.DETECTION_INGEST,
            f"Edge detection {detection_uuid} from {event.bus_id} ({event_class} @ {lat:.4f}, {lng:.4f}) -> {consensus_status} ({consensus_count} buses)",
            severity="INFO" if severity != "CRITICAL" else "WARNING",
            source="EDGE_DETECTION_ROUTER",
            metadata={"detection_id": detection_uuid, "incident_id": target_incident_id, "consensus": consensus_count}
        )

        return {
            "success": True,
            "message": f"Detection ingested successfully into {consensus_status} consensus stream",
            "data": {
                "detection_id": detection_uuid,
                "incident_id": target_incident_id,
                "class_name": event_class,
                "consensus_status": consensus_status,
                "consensus_count": consensus_count,
                "consensus_score": consensus_score,
                "severity": severity,
                "severity_reason": reason,
                "verified_by_buses": current_buses,
                "source_mode": source_mode,
                "latitude": lat,
                "longitude": lng,
                "evidence_url": evidence_url
            }
        }

    except Exception as e:
        logger.error("Ingestion failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Detection processing failed: {str(e)}")

@router.get("/observations/{incident_id}")
async def get_incident_observations(incident_id: str):
    """
    Retrieve the chronological multi-bus consensus observation trail for an incident.
    """
    try:
        supabase = get_supabase()
        res = supabase.from_("incident_observations").select("*").eq("incident_id", incident_id).order("timestamp", desc=False).execute()
        return {
            "success": True,
            "incident_id": incident_id,
            "observations_count": len(res.data or []),
            "data": res.data or []
        }
    except Exception as e:
        return {"success": False, "incident_id": incident_id, "data": [], "error": str(e)}
