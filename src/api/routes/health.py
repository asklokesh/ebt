"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter, Depends

from src.api.dependencies import get_db
from src.core.config import settings
from src.data.database import Database

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    db: Database = Depends(get_db),
) -> dict:
    """
    Health check endpoint.

    Returns:
        Health status dict
    """
    # Check database connectivity
    db_status = "healthy"
    try:
        await db.fetch_one("SELECT 1")
    except Exception:
        db_status = "unhealthy"

    # Check configuration
    config_status = {
        "gemini_configured": settings.is_gemini_configured,
        "usda_configured": settings.is_usda_configured,
    }

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": db_status,
            "configuration": config_status,
        },
    }


@router.get("/")
async def root() -> dict:
    """
    Root endpoint.

    Returns:
        API information
    """
    return {
        "name": "EBT Eligibility Classification API",
        "version": "1.0.0",
        "description": "AI-powered SNAP/EBT eligibility classification system",
        "documentation": "/docs",
        "health": "/health",
    }
