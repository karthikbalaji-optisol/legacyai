from fastapi import APIRouter, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from backend.app.core.config import settings

router = APIRouter(tags=["Health & Telemetry"])

@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Kubernetes / container liveness probe."""
    return {"status": "alive", "service": settings.APP_NAME, "version": settings.APP_VERSION}

@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_probe():
    """Readiness probe checking storage directories and configuration."""
    ready = settings.STORAGE_DIR.exists() and settings.REPOSITORIES_DIR.exists()
    if not ready:
        return Response(content='{"status": "not ready"}', status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    return {
        "status": "ready",
        "database": "sqlite/postgresql",
        "bedrock_configured": bool(settings.AWS_ACCESS_KEY_ID or settings.AWS_REGION),
        "bedrock_model": settings.BEDROCK_MODEL_ID
    }

@router.get("/metrics")
async def prometheus_metrics():
    """Exposes Prometheus application metrics for scraping."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
