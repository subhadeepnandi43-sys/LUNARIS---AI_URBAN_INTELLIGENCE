import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LUNARIS AI Mobile Urban Intelligence Backend"
    VERSION: str = "2.7.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment Mode: LIVE or DEMO
    SYSTEM_MODE: str = os.getenv("SYSTEM_MODE", "DEMO")  # LIVE or DEMO
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://ecmtwoccsdlhphdlutmz.supabase.co")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_l4l1lR2MLi_WOwtjs4CxTw_yBjCx01G")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_l4l1lR2MLi_WOwtjs4CxTw_yBjCx01G"))
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_SECRET_KEY", ""))
    SUPABASE_JWKS_URL: str = os.getenv("SUPABASE_JWKS_URL", "https://ecmtwoccsdlhphdlutmz.supabase.co/auth/v1/.well-known/jwks.json")
    
    # MediaMTX & Video Stream Settings
    MEDIAMTX_RTSP_URL: str = os.getenv("MEDIAMTX_RTSP_URL", "rtsp://localhost:8554")
    MEDIAMTX_WEBRTC_URL: str = os.getenv("MEDIAMTX_WEBRTC_URL", "http://localhost:8889")
    MEDIAMTX_HLS_URL: str = os.getenv("MEDIAMTX_HLS_URL", "http://localhost:8888")
    MEDIAMTX_API_URL: str = os.getenv("MEDIAMTX_API_URL", "http://localhost:9997")
    
    # Storage bucket for Evidence frames
    EVIDENCE_BUCKET: str = os.getenv("EVIDENCE_BUCKET", "incident-evidence")
    REPAIR_EVIDENCE_BUCKET: str = os.getenv("REPAIR_EVIDENCE_BUCKET", "repair-evidence")

    # Multi-Bus Verification & Consensus Algorithm Thresholds
    DUPLICATE_DISTANCE_THRESHOLD_METERS: float = float(os.getenv("DUPLICATE_DISTANCE_THRESHOLD_METERS", "25.0"))
    DUPLICATE_TIME_WINDOW_HOURS: float = float(os.getenv("DUPLICATE_TIME_WINDOW_HOURS", "72.0"))
    CONSENSUS_VERIFICATION_THRESHOLD: int = int(os.getenv("CONSENSUS_VERIFICATION_THRESHOLD", "3"))
    RESCAN_DISTANCE_THRESHOLD_METERS: float = float(os.getenv("RESCAN_DISTANCE_THRESHOLD_METERS", "25.0"))
    
    # Configurable CORS Allowed Origins
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://lunaris-ai-urban-intelligence.vercel.app",
        "*"
    ]
    
    # Privacy & PII
    RAW_VIDEO_RETENTION_HOURS: int = int(os.getenv("RAW_VIDEO_RETENTION_HOURS", "24"))
    EVIDENCE_RETENTION_DAYS: int = int(os.getenv("EVIDENCE_RETENTION_DAYS", "90"))
    FACE_BLUR: bool = True
    PLATE_BLUR: bool = True
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
