"""
RetailIQ - Ingestion & Extraction Module (pipeline/extract.py)
Handles data extraction from raw CSV or Excel, schema validation, and metadata auditing.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RetailIQ-Extract")

EXPECTED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country"
]


class DataExtractor:
    """Extracts raw transaction datasets and validates source schema."""

    def __init__(self, raw_data_path: str = None):
        if raw_data_path:
            self.file_path = Path(raw_data_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent
            # Prefer fast CSV if present, otherwise look for XLSX
            csv_path = base_dir / "data" / "raw" / "online_retail.csv"
            xlsx_path = base_dir / "data" / "raw" / "online_retail.xlsx"
            fallback_xlsx = base_dir / "online+retail" / "Online Retail.xlsx"

            if csv_path.exists():
                self.file_path = csv_path
            elif xlsx_path.exists():
                self.file_path = xlsx_path
            elif fallback_xlsx.exists():
                self.file_path = fallback_xlsx
            else:
                self.file_path = csv_path

    def inspect_file(self) -> Dict[str, Any]:
        """Inspect file properties before reading."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Source file not found at: {self.file_path}")

        file_stat = self.file_path.stat()
        return {
            "file_name": self.file_path.name,
            "file_path": str(self.file_path.resolve()),
            "file_size_bytes": file_stat.st_size,
            "file_size_mb": round(file_stat.st_size / (1024 * 1024), 2),
            "extension": self.file_path.suffix.lower()
        }

    def extract(self, nrows: int = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Extract dataframe from file and collect metadata."""
        file_info = self.inspect_file()
        logger.info(f"Extracting data from {file_info['file_name']} ({file_info['file_size_mb']} MB)...")

        ext = file_info["extension"]
        if ext == ".csv":
            # Using pyarrow engine if available for ultra-fast reading
            try:
                df = pd.read_csv(self.file_path, nrows=nrows, engine="pyarrow")
            except Exception:
                df = pd.read_csv(self.file_path, nrows=nrows, low_memory=False)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(self.file_path, nrows=nrows)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Validate schema
        missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Schema validation failure: Missing columns {missing_cols}")

        metadata = {
            **file_info,
            "raw_row_count": len(df),
            "raw_column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        logger.info(f"Extracted {len(df):,} records across {len(df.columns)} columns.")
        return df, metadata


if __name__ == "__main__":
    extractor = DataExtractor()
    df, meta = extractor.extract(nrows=100)
    print("Extraction successful. Sample metadata:")
    print(meta)
