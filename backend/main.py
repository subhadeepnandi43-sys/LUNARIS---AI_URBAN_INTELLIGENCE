import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import (
    detections,
    fleet,
    incidents,
    streams,
    complaints,
    analytics,
    maintenance,
    traffic,
    pedestrian,
    consensus,
    health,
    notifications
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("lunaris.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI Central Server for LUNARIS Mobile Urban AI Platform (SIH 2026 Problem SIH26124)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware with configurable allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API v1 Prefixed Routers
app.include_router(detections.router, prefix=settings.API_V1_PREFIX)
app.include_router(fleet.router, prefix=settings.API_V1_PREFIX)
app.include_router(incidents.router, prefix=settings.API_V1_PREFIX)
app.include_router(maintenance.router, prefix=settings.API_V1_PREFIX)
app.include_router(consensus.router, prefix=settings.API_V1_PREFIX)
app.include_router(traffic.router, prefix=settings.API_V1_PREFIX)
app.include_router(pedestrian.router, prefix=settings.API_V1_PREFIX)
app.include_router(streams.router, prefix=settings.API_V1_PREFIX)
app.include_router(complaints.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)

# 2. Root-Level Direct Aliases (matching SIH Step 7 specifications)
# /health, /detections, /telemetry, /incidents, /consensus, /traffic, /complaints, /work-orders, /maintenance, /analytics, /notifications
app.include_router(detections.router, prefix="/detections", tags=["Direct Detections"])
app.include_router(fleet.router, prefix="/telemetry", tags=["Direct Telemetry"])
app.include_router(incidents.router, prefix="/incidents", tags=["Direct Incidents"])
app.include_router(maintenance.router, prefix="/maintenance", tags=["Direct Maintenance"])
app.include_router(maintenance.router, prefix="/work-orders", tags=["Direct Work Orders"])
app.include_router(consensus.router, prefix="/consensus", tags=["Direct Consensus"])
app.include_router(traffic.router, prefix="/traffic", tags=["Direct Traffic"])
app.include_router(complaints.router, prefix="/complaints", tags=["Direct Complaints"])
app.include_router(analytics.router, prefix="/analytics", tags=["Direct Analytics"])
app.include_router(notifications.router, prefix="/notifications", tags=["Direct Notifications"])
app.include_router(health.router, prefix="/health", tags=["Direct Health"])

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mode": settings.SYSTEM_MODE,
        "status": "OPERATIONAL",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
        "endpoints": [
            "/health",
            "/detections",
            "/telemetry",
            "/incidents",
            "/consensus",
            "/traffic",
            "/complaints",
            "/work-orders",
            "/maintenance",
            "/analytics",
            "/notifications"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
