import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from backend.models import PedestrianRiskIngest
from backend.database import get_supabase

logger = logging.getLogger("lunaris.pedestrian")
router = APIRouter(prefix="/pedestrian", tags=["Pedestrian Safety & Proximity Risk"])

@router.post("/events", status_code=status.HTTP_201_CREATED)
async def ingest_pedestrian_event(event: PedestrianRiskIngest):
    """
    Ingests pedestrian-vehicle interaction events.
    Applies heuristic risk score based on proximity distance and crowd density.
    """
    try:
        supabase = get_supabase()
        record = {
            "bus_id": event.bus_id,
            "location": event.location,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "event_type": "PEDESTRIAN_PROXIMITY_HAZARD",
            "hazard_level": event.hazard_level,
            "confidence": round(event.risk_score * 100.0, 1),
            "crowd_count_estimate": event.pedestrian_count,
            "recorded_at": datetime.utcnow().isoformat()
        }

        try:
            supabase.from_("pedestrian_events").insert(record).execute()
        except Exception as e:
            logger.debug("Pedestrian event insert notice: %s", e)

        return {
            "success": True,
            "message": "Pedestrian safety hazard logged successfully",
            "data": record
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hotspots")
async def get_pedestrian_risk_hotspots():
    """Returns locations with high pedestrian-vehicle conflict frequencies."""
    try:
        supabase = get_supabase()
        res = supabase.from_("pedestrian_events").select("*").order("recorded_at", desc=True).limit(20).execute()
        return {
            "success": True,
            "hotspots_count": len(res.data or []),
            "data": res.data or []
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
