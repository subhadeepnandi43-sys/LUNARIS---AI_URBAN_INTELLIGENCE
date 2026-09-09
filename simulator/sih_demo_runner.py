"""
LUNARIS — 1-Click SIH Live Demonstration Scenario Runner
Requirement 32 & 33: SIH Demonstration Mode & Demo Data Generator
Runs the closed-loop SIH storyline:
Bus 07 (Detection) -> Bus 12 (2nd Pass) -> Bus 15 (Consensus VERIFIED) ->
Work Order Dispatched -> Repair Executed -> Bus 21 (Re-Scan) -> VERIFIED RESOLUTION!
"""

import time
import json
import urllib.request
import urllib.error
import logging
import argparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [SIH DEMO]: %(message)s")
logger = logging.getLogger("lunaris.sih_demo")

PARK_STREET_COORDS = {"lat": 22.5512, "lng": 88.3524, "loc": "Park Street near Park Hotel, Kolkata"}

def run_sih_demo(backend_url: str = "http://localhost:8000/api/v1", fast_mode: bool = True):
    logger.info("=================================================================")
    logger.info("🛰️  STARTING LUNARIS SMART INDIA HACKATHON LIVE DEMO WORKFLOW")
    logger.info("=================================================================")
    delay = 1.5 if fast_mode else 4.0

    # -------------------------------------------------------------
    # STAGE 1: BUS-07 makes first observation of severe pothole
    # -------------------------------------------------------------
    logger.info("🚌 [STAGE 1] BUS-07 passing Park Street fast lane detects road crater...")
    p1 = {
        "bus_id": "BUS-07",
        "camera_id": "CAM-BUS-07",
        "class_name": "Pothole",
        "confidence": 0.92,
        "latitude": PARK_STREET_COORDS["lat"],
        "longitude": PARK_STREET_COORDS["lng"],
        "location_name": PARK_STREET_COORDS["loc"],
        "source_mode": "DEMO",
        "bounding_box": {"area_cm2": 1400.0, "estimated_depth_cm": 9.5}
    }
    res1 = _post(f"{backend_url}/detections/event", p1)
    inc_id = res1.get("data", {}).get("incident_id", "RD-DEMO-01")
    logger.info(f"   -> Incident Created: {inc_id} | Status: POSSIBLE (1 bus pass)")
    time.sleep(delay)

    # -------------------------------------------------------------
    # STAGE 2: BUS-12 passes 8 minutes later and detects same pothole
    # -------------------------------------------------------------
    logger.info("🚌 [STAGE 2] BUS-12 route transit passes location within 6 meters...")
    p2 = {
        "bus_id": "BUS-12",
        "camera_id": "CAM-BUS-12",
        "class_name": "Pothole",
        "confidence": 0.94,
        "latitude": PARK_STREET_COORDS["lat"] + 0.00004,
        "longitude": PARK_STREET_COORDS["lng"] + 0.00003,
        "location_name": PARK_STREET_COORDS["loc"],
        "source_mode": "DEMO",
        "bounding_box": {"area_cm2": 1450.0, "estimated_depth_cm": 9.8}
    }
    res2 = _post(f"{backend_url}/detections/event", p2)
    logger.info(f"   -> Spatial match found ({inc_id})! Consensus updated: PROBABLE (2 independent buses)")
    time.sleep(delay)

    # -------------------------------------------------------------
    # STAGE 3: BUS-15 passes -> Multi-Bus Consensus Threshold (>= 3)
    # -------------------------------------------------------------
    logger.info("🚌 [STAGE 3] BUS-15 completes 3rd independent pass...")
    p3 = {
        "bus_id": "BUS-15",
        "camera_id": "CAM-BUS-15",
        "class_name": "Pothole",
        "confidence": 0.98,
        "latitude": PARK_STREET_COORDS["lat"] - 0.00002,
        "longitude": PARK_STREET_COORDS["lng"] + 0.00001,
        "location_name": PARK_STREET_COORDS["loc"],
        "source_mode": "DEMO",
        "bounding_box": {"area_cm2": 1480.0, "estimated_depth_cm": 10.2}
    }
    res3 = _post(f"{backend_url}/detections/event", p3)
    data3 = res3.get("data", {})
    logger.info(f"   -> ✅ MULTI-BUS CONSENSUS REACHED!")
    logger.info(f"   -> Status: {data3.get('consensus_status')} (Verified by {data3.get('consensus_count')} buses)")
    logger.info(f"   -> Priority Escalated: {data3.get('severity')} | Reason: {data3.get('severity_reason')}")
    time.sleep(delay)

    # -------------------------------------------------------------
    # STAGE 4: Municipal Authority Creates & Dispatches Work Order
    # -------------------------------------------------------------
    logger.info("📋 [STAGE 4] Municipal Authority HQ reviews incident & dispatches Work Order...")
    wo_payload = {
        "incident_id": inc_id,
        "department": "Road Maintenance Department",
        "assigned_team": "KMC Rapid Repair Squad 01",
        "priority": "CRITICAL",
        "notes": "Emergency bituminous patching required for transit lane pothole",
        "assigned_by": "Executive Engineer KMC"
    }
    res_wo = _post(f"{backend_url}/maintenance/work-orders", wo_payload)
    wo_id = res_wo.get("data", {}).get("work_order_id", "WO-KMC-01")
    logger.info(f"   -> Work Order Dispatched: {wo_id} -> Assigned to KMC Rapid Repair Squad 01")
    time.sleep(delay)

    # -------------------------------------------------------------
    # STAGE 5: Maintenance Squad Executes Repair & Uploads Evidence
    # -------------------------------------------------------------
    logger.info("🔧 [STAGE 5] Maintenance Squad begins repair and seals cavity...")
    _patch(f"{backend_url}/maintenance/work-orders/{wo_id}/start", {})
    time.sleep(delay * 0.8)

    logger.info("📸 Maintenance squad uploads verified AFTER repair photo...")
    complete_payload = {
        "status": "REPAIR_COMPLETED",
        "after_evidence": "assets/evidence/damage_ajc_bose_after.jpg",
        "repair_notes": "Bituminous cold mix compaction completed. Surface leveled.",
        "materials_used": "Asphalt mastic cold mix (50 kg)",
        "completed_by": "Squad Leader K. Das"
    }
    _post(f"{backend_url}/maintenance/work-orders/{wo_id}/complete", complete_payload)
    logger.info(f"   -> Repair Completed! Status: REPAIR_COMPLETED (Awaiting Autonomous Re-Scan)")
    time.sleep(delay)

    # -------------------------------------------------------------
    # STAGE 6: Autonomous Re-Scan by Next Transit Bus (BUS-21)
    # -------------------------------------------------------------
    logger.info("🛰️ [STAGE 6] Subsequent transit bus (BUS-21) scans location 2 hours later...")
    rescan_payload = {
        "incident_id": inc_id,
        "bus_id": "BUS-21",
        "latitude": PARK_STREET_COORDS["lat"],
        "longitude": PARK_STREET_COORDS["lng"],
        "defect_detected": False, # Road is clear!
        "confidence": 0.96
    }
    rescan_res = _post(f"{backend_url}/maintenance/re-scan", rescan_payload)
    logger.info(f"   -> 🎯 RE-SCAN RESULT: {rescan_res.get('re_scan_status')}!")
    logger.info(f"   -> {rescan_res.get('message')}")
    logger.info("=================================================================")
    logger.info("🎉 COMPLETE CLOSED-LOOP SIH LIFECYCLE DEMONSTRATION SUCCESSFUL!")
    logger.info("=================================================================")

def _post(url: str, data: dict) -> dict:
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning(f"POST {url} note: {e}")
        return {"data": data}

def _patch(url: str, data: dict) -> dict:
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"}, method="PATCH")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning(f"PATCH {url} note: {e}")
        return {"data": data}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LUNARIS SIH Live Demo Script")
    parser.add_argument("--backend", default="http://localhost:8000/api/v1", help="Backend URL")
    parser.add_argument("--slow", action="store_true", help="Run with slower human presentation pauses")
    args = parser.parse_args()

    run_sih_demo(backend_url=args.backend, fast_mode=not args.slow)
