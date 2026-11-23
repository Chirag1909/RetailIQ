"""
RetailIQ - Health & Metadata Endpoints (backend/app/api/health.py)
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import HealthResponse, MetadataResponse
from backend.app.core.config import settings

router = APIRouter(tags=["Health & System"])


@router.get("/health", response_model=HealthResponse)
def check_health(db: Session = Depends(get_db)):
    """System health check and database connectivity probe."""
    db_ok = False
    try:
        db.execute(text("SELECT 1;"))
        db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        database_connected=db_ok,
        timestamp=datetime.utcnow().isoformat(),
        environment="production"
    )


@router.get("/metadata", response_model=MetadataResponse)
def get_metadata():
    """Application metadata, dataset provenance, and ML capabilities."""
    return MetadataResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESCRIPTION,
        dataset_source="UCI Machine Learning Repository - Online Retail Dataset",
        supported_models=[
            "Seasonal Naive Baseline",
            "Holt-Winters Exponential Smoothing",
            "XGBoost Lag-Based Regressor"
        ],
        forecast_horizons=[7, 30, 90]
    )
