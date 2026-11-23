"""
RetailIQ - Pipeline Orchestration & Health Endpoints (backend/app/api/pipeline.py)
Enables triggering manual ETL execution, checking real-time status, and inspecting audit logs.
"""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import (
    PipelineStatusResponse, PipelineRunItem
)
from pipeline.run_pipeline import PipelineOrchestrator

router = APIRouter(prefix="/pipeline", tags=["Data Engineering Pipeline"])


def run_pipeline_task():
    """Background task wrapper for ETL execution."""
    orchestrator = PipelineOrchestrator(triggered_by="API_UI")
    orchestrator.execute()


@router.post("/run")
def trigger_pipeline_run(background_tasks: BackgroundTasks):
    """Triggers manual execution of the 7-stage ETL pipeline."""
    background_tasks.add_task(run_pipeline_task)
    return {
        "status": "QUEUED",
        "message": "ETL Pipeline execution successfully triggered in background.",
        "triggered_at": datetime.utcnow().isoformat()
    }


@router.get("/status", response_model=PipelineStatusResponse)
def get_pipeline_status(db: Session = Depends(get_db)):
    """Returns status of most recent execution run and overall pipeline health."""
    row = db.execute(text("""
        SELECT 
            run_id, pipeline_name, status, started_at, completed_at,
            records_extracted, records_cleaned, records_loaded,
            data_quality_score, execution_duration_sec, error_message, triggered_by
        FROM pipeline_runs
        ORDER BY started_at DESC LIMIT 1;
    """)).fetchone()

    total_runs = db.execute(text("SELECT COUNT(*) FROM pipeline_runs;")).scalar() or 0

    latest_run = None
    last_score = 95.0
    sys_health = "HEALTHY"

    if row:
        last_score = float(row[8] or 95.0)
        sys_health = "HEALTHY" if row[2] == "SUCCESS" else "DEGRADED"
        latest_run = PipelineRunItem(
            run_id=row[0],
            pipeline_name=row[1],
            status=row[2],
            started_at=str(row[3]),
            completed_at=str(row[4]) if row[4] else None,
            records_extracted=int(row[5] or 0),
            records_cleaned=int(row[6] or 0),
            records_loaded=int(row[7] or 0),
            data_quality_score=float(row[8]) if row[8] is not None else None,
            execution_duration_sec=float(row[9]) if row[9] is not None else None,
            error_message=row[10],
            triggered_by=row[11]
        )

    return PipelineStatusResponse(
        latest_run=latest_run,
        total_runs=total_runs,
        system_health=sys_health,
        last_quality_score=last_score
    )


@router.get("/history", response_model=List[PipelineRunItem])
def get_pipeline_history(db: Session = Depends(get_db)):
    """Returns chronological audit log of all ETL pipeline runs."""
    rows = db.execute(text("""
        SELECT 
            run_id, pipeline_name, status, started_at, completed_at,
            records_extracted, records_cleaned, records_loaded,
            data_quality_score, execution_duration_sec, error_message, triggered_by
        FROM pipeline_runs
        ORDER BY started_at DESC LIMIT 20;
    """)).fetchall()

    return [
        PipelineRunItem(
            run_id=r[0],
            pipeline_name=r[1],
            status=r[2],
            started_at=str(r[3]),
            completed_at=str(r[4]) if r[4] else None,
            records_extracted=int(r[5] or 0),
            records_cleaned=int(r[6] or 0),
            records_loaded=int(r[7] or 0),
            data_quality_score=float(r[8]) if r[8] is not None else None,
            execution_duration_sec=float(r[9]) if r[9] is not None else None,
            error_message=r[10],
            triggered_by=r[11]
        )
        for r in rows
    ]
