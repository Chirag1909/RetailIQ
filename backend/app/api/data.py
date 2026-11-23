"""
RetailIQ - Data Ingestion & Quality Audit Endpoints (backend/app/api/data.py)
Handles file uploads, source schema verification, and data quality scorecard retrieval.
"""

import json
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pipeline.extract import DataExtractor

router = APIRouter(prefix="/data", tags=["Data Management"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


@router.post("/upload")
async def upload_csv_dataset(file: UploadFile = File(...)):
    """Uploads a CSV or Excel dataset, validates schema, and stages for ingestion."""
    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported.")

    raw_dir = BASE_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / f"uploaded_{file.filename}"

    with open(destination, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Validate uploaded file schema
    try:
        extractor = DataExtractor(str(destination))
        df, meta = extractor.extract(nrows=10)
        return {
            "status": "UPLOADED",
            "file_name": file.filename,
            "staged_path": str(destination.resolve()),
            "columns_detected": meta["columns"],
            "sample_records": len(df),
            "message": "Dataset successfully verified and staged for pipeline processing."
        }
    except Exception as e:
        if destination.exists():
            destination.unlink()
        raise HTTPException(status_code=422, detail=f"Uploaded file failed schema verification: {str(e)}")


@router.get("/quality-report")
def get_data_quality_report():
    """Returns the latest comprehensive Data Quality and Validation Scorecard."""
    report_file = BASE_DIR / "data" / "reports" / "data_quality_report.json"
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Data quality report not generated yet. Run pipeline first.")

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
