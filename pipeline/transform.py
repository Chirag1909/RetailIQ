"""
RetailIQ - Data Transformation & Cleaning Module (pipeline/transform.py)
Implements robust data cleaning, validation tracking, business rule application,
and feature generation for the UCI Online Retail dataset.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RetailIQ-Transform")

NON_PRODUCT_CODES = {
    "POST", "D", "DOT", "M", "CR", "BANK CHARGES", "AMAZONFEE", "S", "GIFT", "PADS"
}


class DataCleaner:
    """Cleans, normalizes, and enriches raw retail transactions."""

    def __init__(self):
        self.audit_log: Dict[str, Any] = {}

    def clean_transactions(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes full data cleaning pipeline with comprehensive auditing.
        
        Cleaning Decisions:
        1. Exact Duplicates: Detected and removed to prevent double-counting.
        2. Invoices: Cast to string, strip whitespace. Identify cancellations (InvoiceNo starting with 'C').
        3. StockCodes: Cast to string, strip whitespace, flag non-merchandise codes (POST, D, CR, etc.).
        4. CustomerID: Convert to integer representation where present; identify nulls as Guest/Unregistered.
        5. Negative Quantities: Segregated into cancellations vs inventory adjustments/scrap.
        6. Invalid Unit Prices: Filter out UnitPrice <= 0 (e.g. system adjustments, zero-price testing).
        7. InvoiceDate: Parsed to standardized UTC timestamp.
        8. Revenue: Computed as Quantity * UnitPrice.
        """
        initial_count = len(df)
        logger.info(f"Initiating data cleaning on {initial_count:,} raw records...")

        # 1. Duplicates check
        duplicate_mask = df.duplicated()
        duplicate_count = int(duplicate_mask.sum())
        df_clean = df.drop_duplicates().copy()
        logger.info(f"Removed {duplicate_count:,} duplicate records.")

        # 2. String standardization
        df_clean["InvoiceNo"] = df_clean["InvoiceNo"].astype(str).str.strip()
        df_clean["StockCode"] = df_clean["StockCode"].astype(str).str.strip().str.upper()
        df_clean["Description"] = df_clean["Description"].fillna("UNKNOWN ITEM").astype(str).str.strip()
        df_clean["Country"] = df_clean["Country"].fillna("Unspecified").astype(str).str.strip()

        # 3. Identify Cancellations
        df_clean["is_cancellation"] = df_clean["InvoiceNo"].str.startswith("C")
        cancellation_count = int(df_clean["is_cancellation"].sum())
        logger.info(f"Identified {cancellation_count:,} cancellation records.")

        # 4. Handle CustomerID (Guest vs Registered)
        missing_customer_count = int(df_clean["CustomerID"].isna().sum())
        df_clean["is_guest"] = df_clean["CustomerID"].isna()
        # For non-null CustomerID, convert float to int string
        df_clean["customer_id_clean"] = df_clean["CustomerID"].apply(
            lambda x: str(int(x)) if pd.notnull(x) else None
        )

        # 5. Non-product / System codes
        df_clean["is_product"] = ~df_clean["StockCode"].isin(NON_PRODUCT_CODES)
        non_product_count = int((~df_clean["is_product"]).sum())

        # 6. Date conversions
        df_clean["InvoiceDate"] = pd.to_datetime(df_clean["InvoiceDate"], errors="coerce")
        invalid_dates_count = int(df_clean["InvoiceDate"].isna().sum())

        # 7. Quantity & UnitPrice validation
        invalid_price_count = int((df_clean["UnitPrice"] <= 0).sum())
        negative_qty_count = int((df_clean["Quantity"] <= 0).sum())

        # Valid completed sales definition:
        # - Not a cancellation
        # - Quantity > 0
        # - UnitPrice > 0
        # - Valid InvoiceDate
        # - Is merchandise product
        valid_sales_mask = (
            (~df_clean["is_cancellation"]) &
            (df_clean["Quantity"] > 0) &
            (df_clean["UnitPrice"] > 0) &
            (df_clean["InvoiceDate"].notna()) &
            (df_clean["is_product"])
        )

        df_sales = df_clean[valid_sales_mask].copy()

        # Calculate revenue
        df_sales["Revenue"] = (df_sales["Quantity"] * df_sales["UnitPrice"]).round(2)
        df_sales["Date"] = df_sales["InvoiceDate"].dt.date
        df_sales["YearMonth"] = df_sales["InvoiceDate"].dt.to_period("M").astype(str)
        df_sales["DayOfWeek"] = df_sales["InvoiceDate"].dt.dayofweek
        df_sales["DayName"] = df_sales["InvoiceDate"].dt.day_name()
        df_sales["Hour"] = df_sales["InvoiceDate"].dt.hour
        df_sales["IsWeekend"] = df_sales["DayOfWeek"].isin([5, 6]).astype(int)

        total_cleaned_sales = len(df_sales)
        total_revenue = float(df_sales["Revenue"].sum())

        # Calculate Data Quality Score (0 - 100)
        # Deduct penalties for duplicates, invalid prices, negative non-cancellations
        dup_penalty = (duplicate_count / initial_count) * 20
        price_penalty = (invalid_price_count / initial_count) * 30
        missing_cust_pct = (missing_customer_count / initial_count) * 100
        quality_score = max(0.0, min(100.0, 100.0 - dup_penalty - price_penalty - (missing_cust_pct * 0.15)))

        self.audit_log = {
            "initial_raw_records": initial_count,
            "duplicate_records_removed": duplicate_count,
            "cancellation_records": cancellation_count,
            "missing_customer_ids": missing_customer_count,
            "missing_customer_pct": round((missing_customer_count / initial_count) * 100, 2),
            "invalid_unit_prices": invalid_price_count,
            "negative_quantities": negative_qty_count,
            "non_merchandise_codes": non_product_count,
            "invalid_dates": invalid_dates_count,
            "valid_completed_sales": total_cleaned_sales,
            "data_retention_rate_pct": round((total_cleaned_sales / initial_count) * 100, 2),
            "total_revenue": round(total_revenue, 2),
            "min_date": str(df_sales["InvoiceDate"].min()),
            "max_date": str(df_sales["InvoiceDate"].max()),
            "unique_products": int(df_sales["StockCode"].nunique()),
            "unique_customers": int(df_sales["customer_id_clean"].dropna().nunique()),
            "unique_countries": int(df_sales["Country"].nunique()),
            "data_quality_score": round(quality_score, 1)
        }

        logger.info(
            f"Cleaning completed: {total_cleaned_sales:,} valid transactions "
            f"(${total_revenue:,.2f} total revenue). Quality Score: {self.audit_log['data_quality_score']}/100"
        )
        return df_sales, self.audit_log

    def generate_aggregates(self, df_sales: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Generate pre-aggregated dimensional summary datasets for high-performance querying."""
        logger.info("Computing daily, monthly, product, and customer aggregates...")

        # 1. Daily Sales Aggregate
        daily_sales = df_sales.groupby("Date").agg(
            revenue=("Revenue", "sum"),
            orders=("InvoiceNo", "nunique"),
            quantity=("Quantity", "sum"),
            unique_customers=("customer_id_clean", "nunique"),
            avg_order_value=("Revenue", lambda x: round(x.sum() / max(1, df_sales.loc[x.index, "InvoiceNo"].nunique()), 2))
        ).reset_index()
        daily_sales["revenue"] = daily_sales["revenue"].round(2)
        daily_sales["Date"] = pd.to_datetime(daily_sales["Date"])

        # 2. Monthly Sales Aggregate
        monthly_sales = df_sales.groupby("YearMonth").agg(
            revenue=("Revenue", "sum"),
            orders=("InvoiceNo", "nunique"),
            quantity=("Quantity", "sum"),
            unique_customers=("customer_id_clean", "nunique")
        ).reset_index()
        monthly_sales["revenue"] = monthly_sales["revenue"].round(2)
        monthly_sales = monthly_sales.sort_values("YearMonth").reset_index(drop=True)
        # Month-over-month growth rate (%)
        monthly_sales["mom_growth_pct"] = (
            monthly_sales["revenue"].pct_change() * 100
        ).round(2).fillna(0.0)

        # 3. Product Metrics Aggregate
        product_metrics = df_sales.groupby("StockCode").agg(
            description=("Description", "first"),
            total_revenue=("Revenue", "sum"),
            total_quantity=("Quantity", "sum"),
            order_count=("InvoiceNo", "nunique"),
            avg_unit_price=("UnitPrice", "mean"),
            first_sold_date=("InvoiceDate", "min"),
            last_sold_date=("InvoiceDate", "max")
        ).reset_index()
        product_metrics["total_revenue"] = product_metrics["total_revenue"].round(2)
        product_metrics["avg_unit_price"] = product_metrics["avg_unit_price"].round(2)
        product_metrics = product_metrics.sort_values("total_revenue", ascending=False).reset_index(drop=True)

        # 4. Customer Metrics (identified customers only)
        identified = df_sales[df_sales["customer_id_clean"].notna()].copy()
        reference_date = df_sales["InvoiceDate"].max() + pd.Timedelta(days=1)

        customer_metrics = identified.groupby("customer_id_clean").agg(
            country=("Country", "first"),
            first_order_date=("InvoiceDate", "min"),
            last_order_date=("InvoiceDate", "max"),
            order_count=("InvoiceNo", "nunique"),
            total_spend=("Revenue", "sum"),
            total_units=("Quantity", "sum")
        ).reset_index()
        customer_metrics["total_spend"] = customer_metrics["total_spend"].round(2)
        customer_metrics["avg_order_value"] = (
            customer_metrics["total_spend"] / customer_metrics["order_count"]
        ).round(2)
        customer_metrics["recency_days"] = (
            (reference_date - customer_metrics["last_order_date"]).dt.days
        )
        customer_metrics.rename(columns={"customer_id_clean": "customer_id"}, inplace=True)

        logger.info("Aggregates successfully generated.")
        return {
            "daily_sales": daily_sales,
            "monthly_sales": monthly_sales,
            "product_metrics": product_metrics,
            "customer_metrics": customer_metrics
        }


def run_transformation(raw_csv_path: str = None) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], Dict[str, Any]]:
    """Runs extraction, cleaning, and aggregate persistence."""
    from pipeline.extract import DataExtractor

    extractor = DataExtractor(raw_csv_path)
    raw_df, meta = extractor.extract()

    cleaner = DataCleaner()
    df_sales, audit = cleaner.clean_transactions(raw_df)
    aggregates = cleaner.generate_aggregates(df_sales)

    # Save cleaned files to data/processed
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    df_sales.to_csv(processed_dir / "cleaned_transactions.csv", index=False)
    aggregates["daily_sales"].to_csv(processed_dir / "daily_sales.csv", index=False)
    aggregates["monthly_sales"].to_csv(processed_dir / "monthly_sales.csv", index=False)
    aggregates["product_metrics"].to_csv(processed_dir / "product_metrics.csv", index=False)
    aggregates["customer_metrics"].to_csv(processed_dir / "customer_metrics.csv", index=False)

    logger.info(f"Cleaned datasets and aggregates saved to {processed_dir}")
    return df_sales, aggregates, audit


if __name__ == "__main__":
    df_sales, aggs, audit = run_transformation()
    print("\n--- DATA CLEANING AUDIT REPORT ---")
    for k, v in audit.items():
        print(f"  {k}: {v}")
