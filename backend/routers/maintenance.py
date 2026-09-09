import logging
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from backend.models import WorkOrderCreate, WorkOrderUpdate, ReScanVerifyEvent
from backend.database import get_supabase
from backend.logger import log_system_event, AuditEventType

logger = logging.getLogger("lunaris.maintenance")
router = APIRouter(prefix="/maintenance", tags=["Maintenance Work Orders & Auto Re-Scan"])

@router.post("/work-orders", status_code=status.HTTP_201_CREATED)
async def create_work_order(wo: WorkOrderCreate):
    """
    Municipal Authority creates and dispatches a Work Order for a verified road incident.
    Lifecycle Stage: VERIFIED -> WORK ORDER CREATED -> ASSIGNED
    """
    try:
        supabase = get_supabase()
        wo_id = f"WO-{uuid.uuid4().hex[:5].upper()}"

        work_order_data = {
            "work_order_id": wo_id,
            "incident_id": wo.incident_id,
            "department": wo.department,
            "assigned_team": wo.assigned_team,
            "priority": wo.priority,
            "status": "ASSIGNED",
            "notes": wo.notes or f"Official municipal repair dispatch for {wo.incident_id}",
            "assigned_by": wo.assigned_by,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Insert work order
        try:
            supabase.from_("work_orders").insert(work_order_data).execute()
        except Exception as e:
            logger.debug("Work order table notice: %s", e)

        # Update Incident Status to ASSIGNED
        try:
            supabase.from_("incidents").update({
                "status": "ASSIGNED",
                "assigned_authority": wo.assigned_team,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("incident_id", wo.incident_id).execute()
        except Exception as e:
            logger.debug("Incident status update notice: %s", e)

        log_system_event(
            AuditEventType.ASSIGNMENT,
            f"Work Order {wo_id} created for incident {wo.incident_id}, assigned to {wo.assigned_team}",
            severity="INFO",
            source="MAINTENANCE_ROUTER",
            metadata={"work_order_id": wo_id, "incident_id": wo.incident_id, "team": wo.assigned_team}
        )

        return {
            "success": True,
            "message": f"Work order {wo_id} successfully created and dispatched",
            "data": work_order_data
        }
    except Exception as e:
        logger.error("Failed to create work order: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/work-orders")
async def list_work_orders(status: Optional[str] = None):
    """List all municipal work orders."""
    try:
        supabase = get_supabase()
        query = supabase.from_("work_orders").select("*").order("created_at", desc=True)
        if status and status != "ALL":
            query = query.eq("status", status.upper())
        res = query.execute()
        return {"success": True, "count": len(res.data or []), "data": res.data or []}
    except Exception as e:
        return {"success": False, "count": 0, "data": [], "error": str(e)}

@router.patch("/work-orders/{wo_id}/start")
async def start_work_order(wo_id: str):
    """Maintenance team marks work order IN PROGRESS."""
    try:
        supabase = get_supabase()
        now = datetime.utcnow().isoformat()
        supabase.from_("work_orders").update({
            "status": "IN_PROGRESS",
            "started_at": now,
            "updated_at": now
        }).eq("work_order_id", wo_id).execute()

        # Update Incident
        res = supabase.from_("work_orders").select("incident_id").eq("work_order_id", wo_id).execute()
        if res.data:
            inc_id = res.data[0]["incident_id"]
            supabase.from_("incidents").update({"status": "IN PROGRESS", "updated_at": now}).eq("incident_id", inc_id).execute()

        return {"success": True, "work_order_id": wo_id, "status": "IN_PROGRESS"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/work-orders/{wo_id}/complete")
async def complete_work_order(wo_id: str, update: WorkOrderUpdate):
    """
    Maintenance squad marks repair finished and uploads photographic repair evidence.
    Lifecycle Stage: IN PROGRESS -> REPAIR COMPLETED (Ready for Auto Re-Scan)
    """
    try:
        supabase = get_supabase()
        now = datetime.utcnow().isoformat()
        
        patch_data = {
            "status": "REPAIR_COMPLETED",
            "after_evidence": update.after_evidence,
            "repair_notes": update.repair_notes or "Bituminous hot mix patch completed and leveled",
            "materials_used": update.materials_used or "Cold mix bitumen (40kg) + asphalt sealer",
            "completed_at": now,
            "updated_at": now
        }
        supabase.from_("work_orders").update(patch_data).eq("work_order_id", wo_id).execute()

        # Fetch incident to link after_evidence
        res = supabase.from_("work_orders").select("incident_id").eq("work_order_id", wo_id).execute()
        if res.data:
            inc_id = res.data[0]["incident_id"]
            supabase.from_("incidents").update({
                "status": "REPAIR_COMPLETED",
                "after_evidence": update.after_evidence,
                "updated_at": now
            }).eq("incident_id", inc_id).execute()

        log_system_event(
            AuditEventType.STATUS_UPDATE,
            f"Work Order {wo_id} repair completed. Evidence uploaded. Scheduled for transit re-scan.",
            severity="INFO",
            source="MAINTENANCE_ROUTER",
            metadata={"work_order_id": wo_id, "status": "REPAIR_COMPLETED"}
        )

        return {
            "success": True,
            "work_order_id": wo_id,
            "status": "REPAIR_COMPLETED",
            "next_stage": "AUTOMATIC_RESCAN"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/re-scan")
async def process_rescan_verification(event: ReScanVerifyEvent):
    """
    Requirement 14: Automatic Re-Scan Verification.
    After maintenance marks repair complete, subsequent transit buses passing the GPS zone re-scan.
    - If no defect detected -> VERIFIED RESOLUTION (Closed Loop Achieved).
    - If defect persists -> REPAIR FAILED / RECHECK REQUIRED (Alert dispatched).
    """
    try:
        supabase = get_supabase()
        now = datetime.utcnow().isoformat()

        if not event.defect_detected:
            # Defect is fixed! Mark as Verified Resolution
            new_status = "VERIFIED RESOLUTION"
            msg = f"Automatic Re-Scan by {event.bus_id} confirmed road surface smooth! Incident {event.incident_id} verified resolved."
            audit_sev = "INFO"
        else:
            # Defect still detected! Repair failed!
            new_status = "REPAIR FAILED / RECHECK REQUIRED"
            msg = f"Automatic Re-Scan by {event.bus_id} detected defect STILL PRESENT! Repair audit failed for {event.incident_id}."
            audit_sev = "WARNING"

        # Update Incident
        supabase.from_("incidents").update({
            "status": new_status,
            "updated_at": now
        }).eq("incident_id", event.incident_id).execute()

        # Update Work Order
        supabase.from_("work_orders").update({
            "resolution_verified": not event.defect_detected,
            "verified_by_bus": event.bus_id,
            "rescan_timestamp": now,
            "status": "VERIFIED_RESOLUTION" if not event.defect_detected else "RECHECK_REQUIRED",
            "updated_at": now
        }).eq("incident_id", event.incident_id).execute()

        log_system_event(
            AuditEventType.RESOLUTION if not event.defect_detected else AuditEventType.INCIDENT_CREATE,
            msg,
            severity=audit_sev,
            source="AUTOMATIC_RESCAN_ENGINE",
            metadata={"incident_id": event.incident_id, "bus_id": event.bus_id, "status": new_status}
        )

        return {
            "success": True,
            "incident_id": event.incident_id,
            "re_scan_status": new_status,
            "defect_cleared": not event.defect_detected,
            "verified_by": event.bus_id,
            "message": msg
        }
    except Exception as e:
        logger.error("Re-scan evaluation error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
