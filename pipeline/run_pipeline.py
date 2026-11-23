"""
RetailIQ - End-to-End ETL Pipeline Orchestrator (pipeline/run_pipeline.py)
Orchestrates Ingestion, Schema Validation, Cleaning, Dimensional Modeling,
Database Loading, Quality Validation, and Audit Logging with retry handling.
"""

import os
import sys
import time
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
from sqlalchemy import text
from backend.app.database.session import SessionLocal, init_db, engine
from backend.app.models.entities import PipelineRun, DataQualityReport
from pipeline.extract import DataExtractor
from pipeline.transform import DataCleaner
from pipeline.data_quality import DataQualityValidator
from pipeline.load import DatabaseLoader
from pipeline.eda import ExploratoryDataAnalyzer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RetailIQ-Orchestrator")


class PipelineOrchestrator:
    """Enterprise ETL Orchestrator with stage-wise tracking, retries, and execution audits."""

    def __init__(self, raw_data_path: Optional[str] = None, triggered_by: str = "SYSTEM"):
        self.raw_data_path = raw_data_path
        self.triggered_by = triggered_by
        self.run_id = f"RUN-{uuid.uuid4().hex[:12].upper()}"
        self.stages_status = {}

    def execute(self, max_retries: int = 2) -> Dict[str, Any]:
        """Runs the complete 7-stage ETL workflow with error recovery."""
        start_time = time.time()
        started_at = datetime.utcnow()
        logger.info(f"=== Starting RetailIQ ETL Pipeline [{self.run_id}] ===")

        # Initialize DB and log run start
        init_db()
        db = SessionLocal()
        run_record = PipelineRun(
            run_id=self.run_id,
            pipeline_name="RETAILIQ_CORE_ETL",
            status="RUNNING",
            started_at=started_at,
            triggered_by=self.triggered_by
        )
        db.add(run_record)
        db.commit()

        attempt = 0
        while attempt <= max_retries:
            try:
                # Stage 1: Data Ingestion & Extraction
                logger.info("[Stage 1/7] Ingesting source transaction file...")
                extractor = DataExtractor(self.raw_data_path)
                raw_df, extract_meta = extractor.extract()
                self.stages_status["ingestion"] = "SUCCESS"

                # Stage 2: Schema Validation
                logger.info("[Stage 2/7] Validating schema and structure...")
                required_cols = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
                assert all(col in raw_df.columns for col in required_cols), "Schema assertion failed"
                self.stages_status["schema_validation"] = "SUCCESS"

                # Stage 3: Data Cleaning
                logger.info("[Stage 3/7] Cleaning, deduplicating, and standardizing transactions...")
                cleaner = DataCleaner()
                cleaned_df, audit_log = cleaner.clean_transactions(raw_df)
                self.stages_status["data_cleaning"] = "SUCCESS"

                # Stage 4: Feature Engineering & Analytics Aggregation
                logger.info("[Stage 4/7] Generating dimensional aggregates & RFM metrics...")
                aggregates = cleaner.generate_aggregates(cleaned_df)
                self.stages_status["aggregation"] = "SUCCESS"

                # Stage 5: Database Loading (Star Schema)
                logger.info("[Stage 5/7] Bulk loading dimensional star schema tables...")
                loader = DatabaseLoader()
                loader.generate_and_load_dim_date(cleaned_df["InvoiceDate"].min(), cleaned_df["InvoiceDate"].max())
                loader.load_dim_product(aggregates["product_metrics"])
                loader.load_dim_customer(aggregates["customer_metrics"])
                loader.load_fact_sales(cleaned_df)
                loader.load_aggregates(aggregates)
                loader.initialize_inventory_parameters(aggregates["product_metrics"])
                self.stages_status["db_loading"] = "SUCCESS"

                # Stage 6: Quality Validation & Audit Report
                logger.info("[Stage 6/7] Generating data health scorecard...")
                validator = DataQualityValidator(raw_df, cleaned_df, audit_log)
                quality_report = validator.generate_report()
                report_file = validator.save_report()
                self.stages_status["quality_validation"] = "SUCCESS"

                # Stage 7: Persist Processed Artifacts & Sync Reports
                logger.info("[Stage 7/7] Persisting CSV cache & generating EDA artifacts...")
                processed_dir = BASE_DIR / "data" / "processed"
                processed_dir.mkdir(parents=True, exist_ok=True)
                cleaned_df.to_csv(processed_dir / "cleaned_transactions.csv", index=False)
                for name, df_agg in aggregates.items():
                    df_agg.to_csv(processed_dir / f"{name}.csv", index=False)

                # Persist quality report to DB
                dqr_entry = DataQualityReport(
                    report_id=quality_report["report_id"],
                    generated_at=datetime.fromisoformat(quality_report["generated_at"]),
                    overall_quality_score=quality_report["overall_quality_score"],
                    status=quality_report["status"],
                    raw_record_count=quality_report["summary_metrics"]["raw_records"],
                    cleaned_record_count=quality_report["summary_metrics"]["cleaned_records"],
                    retention_rate_pct=quality_report["summary_metrics"]["retention_rate_pct"],
                    duplicate_records=quality_report["anomalies_detected"]["duplicate_rows"],
                    missing_customer_ids=quality_report["anomalies_detected"]["missing_customer_ids"],
                    cancellations_detected=quality_report["anomalies_detected"]["cancellations_flagged"],
                    report_json=str(quality_report)
                )
                db.merge(dqr_entry)

                duration = round(time.time() - start_time, 2)
                run_record.status = "SUCCESS"
                run_record.completed_at = datetime.utcnow()
                run_record.records_extracted = extract_meta["raw_row_count"]
                run_record.records_cleaned = len(cleaned_df)
                run_record.records_loaded = len(cleaned_df)
                run_record.data_quality_score = quality_report["overall_quality_score"]
                run_record.execution_duration_sec = duration
                db.commit()

                logger.info(f"[+] Pipeline [{self.run_id}] completed successfully in {duration}s!")
                return {
                    "run_id": self.run_id,
                    "status": "SUCCESS",
                    "duration_sec": duration,
                    "records_extracted": extract_meta["raw_row_count"],
                    "records_cleaned": len(cleaned_df),
                    "quality_score": quality_report["overall_quality_score"],
                    "stages": self.stages_status
                }

            except Exception as e:
                attempt += 1
                logger.error(f"[!] Pipeline failure on attempt {attempt}: {e}", exc_info=True)
                if attempt > max_retries:
                    duration = round(time.time() - start_time, 2)
                    run_record.status = "FAILED"
                    run_record.completed_at = datetime.utcnow()
                    run_record.error_message = str(e)
                    run_record.execution_duration_sec = duration
                    db.commit()
                    db.close()
                    raise RuntimeError(f"Pipeline execution permanently failed after {max_retries} retries: {e}")
                time.sleep(2)
            finally:
                db.close()


def run_pipeline_cli():
    orchestrator = PipelineOrchestrator(triggered_by="CLI")
    res = orchestrator.execute()
    print("\n--- PIPELINE EXECUTION SUMMARY ---")
    for k, v in res.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    run_pipeline_cli()
