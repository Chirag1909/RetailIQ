"""
RetailIQ - Database Bulk Loader (pipeline/load.py)
Idempotently loads cleaned transactions, dimensions, aggregates, and initial parameters
into the analytical star-schema relational database.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
from sqlalchemy import text
from backend.app.database.session import engine, init_db, SessionLocal
from backend.app.models.entities import (
    DimDate, DimProduct, DimCustomer, FactSale,
    DailySale, MonthlySale, ProductMetric, CustomerMetric,
    InventoryParameter, PipelineRun, DataQualityReport
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RetailIQ-Load")


class DatabaseLoader:
    """Manages idempotent bulk loading of star-schema relational tables."""

    def __init__(self):
        init_db()

    def generate_and_load_dim_date(self, min_date: datetime, max_date: datetime):
        """Populate calendar dimension from min_date to max_date."""
        logger.info(f"Populating dim_date between {min_date.date()} and {max_date.date()}...")
        dates = pd.date_range(min_date.date(), max_date.date(), freq="D")
        date_records = []
        for d in dates:
            date_records.append({
                "date_key": d.date(),
                "year": int(d.year),
                "quarter": int(d.quarter),
                "month": int(d.month),
                "month_name": d.strftime("%B"),
                "year_month": d.strftime("%Y-%m"),
                "day_of_month": int(d.day),
                "day_of_week": int(d.dayofweek),
                "day_name": d.strftime("%A"),
                "is_weekend": 1 if d.dayofweek in [5, 6] else 0,
                "quarter_name": f"{d.year}-Q{d.quarter}"
            })
        df_dim_date = pd.DataFrame(date_records)
        df_dim_date.to_sql("dim_date", con=engine, if_exists="replace", index=False)
        logger.info(f"Loaded {len(df_dim_date):,} records into dim_date.")

    def load_dim_product(self, product_metrics_df: pd.DataFrame):
        """Load product dimension."""
        logger.info("Loading dim_product...")
        prod_dim = product_metrics_df.copy()
        prod_dim.columns = [c.lower() for c in prod_dim.columns]
        if "stockcode" in prod_dim.columns:
            prod_dim.rename(columns={"stockcode": "stock_code"}, inplace=True)
        prod_dim["is_active"] = 1
        prod_dim["created_at"] = datetime.utcnow()
        prod_dim["updated_at"] = datetime.utcnow()
        prod_dim.rename(columns={
            "total_revenue": "total_lifetime_revenue",
            "total_quantity": "total_lifetime_quantity"
        }, inplace=True)

        cols_to_keep = [
            "stock_code", "description", "avg_unit_price",
            "total_lifetime_revenue", "total_lifetime_quantity",
            "first_sold_date", "last_sold_date", "is_active", "created_at", "updated_at"
        ]
        prod_dim = prod_dim[[c for c in cols_to_keep if c in prod_dim.columns]]
        prod_dim.to_sql("dim_product", con=engine, if_exists="replace", index=False)
        logger.info(f"Loaded {len(prod_dim):,} products into dim_product.")

    def load_dim_customer(self, customer_metrics_df: pd.DataFrame):
        """Load customer dimension."""
        logger.info("Loading dim_customer...")
        cust_dim = customer_metrics_df.copy()
        cust_dim["total_orders"] = cust_dim["order_count"]
        cust_dim["created_at"] = datetime.utcnow()
        cust_dim["updated_at"] = datetime.utcnow()
        cust_dim["rfm_recency"] = cust_dim["recency_days"]
        cust_dim["rfm_frequency"] = cust_dim["order_count"]
        cust_dim["rfm_monetary"] = cust_dim["total_spend"]
        cust_dim["rfm_segment"] = cust_dim.get("segment", "Standard")

        cols_to_keep = [
            "customer_id", "country", "first_order_date", "last_order_date",
            "total_orders", "total_spend", "rfm_recency", "rfm_frequency",
            "rfm_monetary", "rfm_segment", "created_at", "updated_at"
        ]
        cust_dim = cust_dim[[c for c in cols_to_keep if c in cust_dim.columns]]
        cust_dim.to_sql("dim_customer", con=engine, if_exists="replace", index=False)
        logger.info(f"Loaded {len(cust_dim):,} customers into dim_customer.")

    def load_fact_sales(self, df_sales: pd.DataFrame, chunksize: int = 50000):
        """Bulk load fact_sales table."""
        logger.info(f"Loading {len(df_sales):,} transactions into fact_sales...")
        fact_df = pd.DataFrame({
            "invoice_no": df_sales["InvoiceNo"].astype(str),
            "stock_code": df_sales["StockCode"].astype(str),
            "customer_id": df_sales["customer_id_clean"],
            "date_key": pd.to_datetime(df_sales["Date"]).dt.date,
            "invoice_date": pd.to_datetime(df_sales["InvoiceDate"]),
            "quantity": df_sales["Quantity"].astype(int),
            "unit_price": df_sales["UnitPrice"].astype(float),
            "line_total": df_sales["Revenue"].astype(float),
            "country": df_sales["Country"].astype(str),
            "is_guest": df_sales["is_guest"].astype(int),
            "created_at": datetime.utcnow()
        })

        fact_df.to_sql("fact_sales", con=engine, if_exists="replace", index=True, index_label="sale_id", chunksize=chunksize)
        logger.info(f"Loaded {len(fact_df):,} records into fact_sales.")

    def load_aggregates(self, aggregates: Dict[str, pd.DataFrame]):
        """Load pre-aggregated tables."""
        logger.info("Loading pre-aggregated summary tables...")

        # daily_sales
        daily = aggregates["daily_sales"].copy()
        daily.rename(columns={
            "Date": "date_key",
            "orders": "order_count",
            "quantity": "quantity_sold"
        }, inplace=True)
        daily["date_key"] = pd.to_datetime(daily["date_key"]).dt.date
        daily["created_at"] = datetime.utcnow()
        daily.to_sql("daily_sales", con=engine, if_exists="replace", index=False)

        # monthly_sales
        monthly = aggregates["monthly_sales"].copy()
        monthly.rename(columns={
            "YearMonth": "year_month",
            "orders": "order_count",
            "quantity": "quantity_sold"
        }, inplace=True)
        monthly["created_at"] = datetime.utcnow()
        monthly.to_sql("monthly_sales", con=engine, if_exists="replace", index=False)

        # product_metrics
        prod_m = aggregates["product_metrics"].copy()
        prod_m.columns = [c.lower() for c in prod_m.columns]
        if "stockcode" in prod_m.columns:
            prod_m.rename(columns={"stockcode": "stock_code"}, inplace=True)
        prod_m["revenue_rank"] = range(1, len(prod_m) + 1)
        prod_m["demand_velocity_category"] = np.where(
            prod_m["revenue_rank"] <= len(prod_m) * 0.1, "High Velocity",
            np.where(prod_m["revenue_rank"] <= len(prod_m) * 0.4, "Medium Velocity", "Low Velocity")
        )
        prod_m["updated_at"] = datetime.utcnow()
        prod_m.to_sql("product_metrics", con=engine, if_exists="replace", index=False)

        # customer_metrics
        cust_m = aggregates["customer_metrics"].copy()
        cust_m["updated_at"] = datetime.utcnow()
        cust_m.to_sql("customer_metrics", con=engine, if_exists="replace", index=False)
        logger.info("Aggregates successfully loaded.")

    def initialize_inventory_parameters(self, product_metrics_df: pd.DataFrame):
        """Initialize inventory parameters with realistic baseline assumptions."""
        logger.info("Initializing inventory parameters and risk metrics...")
        records = []
        for idx, row in product_metrics_df.iterrows():
            avg_daily_qty = max(0.5, row["total_quantity"] / 365.0)
            lead_time = 14
            lead_time_demand = round(avg_daily_qty * lead_time, 2)
            # Service level 95% => Z ~ 1.65, stddev estimation ~ 0.5 * avg
            safety_stock = int(np.ceil(1.65 * np.sqrt(lead_time) * (avg_daily_qty * 0.4)))
            reorder_point = int(np.ceil(lead_time_demand + safety_stock))
            # Simulated current stock between 0.5x and 2.5x of reorder point for operational testing
            simulated_current_stock = int(max(5, reorder_point * (0.8 + (idx % 5) * 0.35)))
            suggested_reorder = max(0, (reorder_point * 2) - simulated_current_stock)
            coverage_days = round(simulated_current_stock / max(0.01, avg_daily_qty), 1)

            if simulated_current_stock < safety_stock:
                risk = "Critical"
            elif simulated_current_stock < reorder_point:
                risk = "High"
            elif coverage_days > 60:
                risk = "Low"
            else:
                risk = "Medium"

            overstock_risk = "High" if coverage_days > 90 else "Medium" if coverage_days > 60 else "Low"
            stock_code = str(row.get("stock_code", row.get("StockCode", "")))

            records.append({
                "stock_code": stock_code,
                "current_stock": simulated_current_stock,
                "lead_time_days": lead_time,
                "service_level_pct": 95.0,
                "holding_cost": 1.50,
                "reorder_cost": 25.00,
                "expected_lead_time_demand": lead_time_demand,
                "safety_stock": safety_stock,
                "reorder_point": reorder_point,
                "suggested_reorder_qty": suggested_reorder,
                "inventory_coverage_days": coverage_days,
                "stockout_risk_level": risk,
                "overstock_risk_level": overstock_risk,
                "last_evaluated_at": datetime.utcnow()
            })

        df_inv = pd.DataFrame(records)
        df_inv.to_sql("inventory_parameters", con=engine, if_exists="replace", index=False)
        logger.info(f"Loaded {len(df_inv):,} inventory parameter configurations.")


def run_load():
    """Execute complete database load from processed artifacts."""
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / "data" / "processed"

    df_sales = pd.read_csv(processed_dir / "cleaned_transactions.csv")
    df_sales["InvoiceDate"] = pd.to_datetime(df_sales["InvoiceDate"])
    df_sales["Date"] = pd.to_datetime(df_sales["Date"])

    daily_sales = pd.read_csv(processed_dir / "daily_sales.csv")
    monthly_sales = pd.read_csv(processed_dir / "monthly_sales.csv")
    product_metrics = pd.read_csv(processed_dir / "product_metrics.csv")
    customer_metrics = pd.read_csv(processed_dir / "customer_metrics.csv")

    aggregates = {
        "daily_sales": daily_sales,
        "monthly_sales": monthly_sales,
        "product_metrics": product_metrics,
        "customer_metrics": customer_metrics
    }

    loader = DatabaseLoader()
    loader.generate_and_load_dim_date(df_sales["InvoiceDate"].min(), df_sales["InvoiceDate"].max())
    loader.load_dim_product(product_metrics)
    loader.load_dim_customer(customer_metrics)
    loader.load_fact_sales(df_sales)
    loader.load_aggregates(aggregates)
    loader.initialize_inventory_parameters(product_metrics)
    logger.info("[+] Full database loading completed successfully!")


if __name__ == "__main__":
    run_load()
