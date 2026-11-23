"""
RetailIQ - Data Quality & Validation Engine (pipeline/data_quality.py)
Generates comprehensive data quality audit reports, health scorecards,
and anomaly analyses for ingestion pipelines.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RetailIQ-DataQuality")


class DataQualityValidator:
    """Validates dataset integrity and produces structured audit reports."""

    def __init__(self, raw_df: pd.DataFrame, cleaned_df: pd.DataFrame, audit_log: Dict[str, Any]):
        self.raw_df = raw_df
        self.cleaned_df = cleaned_df
        self.audit_log = audit_log

    def generate_report(self) -> Dict[str, Any]:
        """Construct full quality scorecard."""
        total_raw = len(self.raw_df)
        total_clean = len(self.cleaned_df)
        retention_rate = round((total_clean / total_raw) * 100, 2) if total_raw > 0 else 0

        # Anomaly checks
        quantity_outliers = int((self.cleaned_df["Quantity"] > 5000).sum())
        unit_price_outliers = int((self.cleaned_df["UnitPrice"] > 500).sum())

        missing_desc = int(self.raw_df["Description"].isna().sum())
        missing_cust = int(self.raw_df["CustomerID"].isna().sum())
        duplicate_rows = int(self.raw_df.duplicated().sum())

        # Formula calculation
        # Max score: 100. Deductions for missing, invalid, duplicates
        completeness_score = max(0.0, 100.0 - (missing_cust / total_raw * 50) - (missing_desc / total_raw * 20))
        validity_score = max(0.0, 100.0 - ((total_raw - total_clean) / total_raw * 40))
        uniqueness_score = max(0.0, 100.0 - (duplicate_rows / total_raw * 100))
        overall_score = round((completeness_score * 0.35 + validity_score * 0.45 + uniqueness_score * 0.20), 1)

        report = {
            "report_id": f"DQR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "overall_quality_score": overall_score,
            "status": "HEALTHY" if overall_score >= 80 else "WARNING" if overall_score >= 60 else "CRITICAL",
            "scoring_breakdown": {
                "completeness_score": round(completeness_score, 1),
                "validity_score": round(validity_score, 1),
                "uniqueness_score": round(uniqueness_score, 1),
                "formula": "Overall = (Completeness * 0.35) + (Validity * 0.45) + (Uniqueness * 0.20)"
            },
            "summary_metrics": {
                "raw_records": total_raw,
                "cleaned_records": total_clean,
                "retention_rate_pct": retention_rate,
                "total_valid_revenue": round(float(self.cleaned_df["Revenue"].sum()), 2),
                "unique_products": int(self.cleaned_df["StockCode"].nunique()),
                "unique_customers": int(self.cleaned_df["customer_id_clean"].dropna().nunique()),
                "unique_countries": int(self.cleaned_df["Country"].nunique())
            },
            "anomalies_detected": {
                "duplicate_rows": duplicate_rows,
                "missing_customer_ids": missing_cust,
                "missing_descriptions": missing_desc,
                "cancellations_flagged": self.audit_log.get("cancellation_records", 0),
                "invalid_or_zero_unit_prices": self.audit_log.get("invalid_unit_prices", 0),
                "negative_quantities": self.audit_log.get("negative_quantities", 0),
                "quantity_outliers_gt_5000": quantity_outliers,
                "unit_price_outliers_gt_500": unit_price_outliers
            },
            "temporal_coverage": {
                "min_date": str(self.cleaned_df["InvoiceDate"].min()),
                "max_date": str(self.cleaned_df["InvoiceDate"].max()),
                "total_days_active": (self.cleaned_df["InvoiceDate"].max() - self.cleaned_df["InvoiceDate"].min()).days
            }
        }
        return report

    def save_report(self, output_dir: Path = None) -> Path:
        """Save report to JSON."""
        if output_dir is None:
            output_dir = Path(__file__).resolve().parent.parent / "data" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        report = self.generate_report()
        report_file = output_dir / "data_quality_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Data quality report successfully saved to {report_file}")
        return report_file


if __name__ == "__main__":
    from pipeline.extract import DataExtractor
    from pipeline.transform import DataCleaner

    extractor = DataExtractor()
    raw_df, _ = extractor.extract()
    cleaner = DataCleaner()
    cleaned_df, audit = cleaner.clean_transactions(raw_df)
    validator = DataQualityValidator(raw_df, cleaned_df, audit)
    validator.save_report()
