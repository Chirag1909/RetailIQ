"""
RetailIQ - Database Configuration & Session Management
Handles SQLAlchemy connection pooling, engine initialization, session lifecycle,
and dual dialect support (PostgreSQL primary with seamless SQLite fallback).
"""

import os
import sys
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_FILE = BASE_DIR / "retailiq.db"

# Read DATABASE_URL from environment or fallback to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Use SQLite file database
    DATABASE_URL = f"sqlite:///{DB_FILE.as_posix()}"

# Configure engine with dialect-specific options
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for thread-safe database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_views_if_needed():
    """Create analytical SQL views compatible with current database dialect."""
    with engine.begin() as conn:
        # SQLite compatible view definitions
        try:
            conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_revenue_by_month AS
            SELECT 
                d.year_month,
                d.year,
                d.month_name,
                COUNT(DISTINCT f.invoice_no) AS total_orders,
                SUM(f.quantity) AS total_units_sold,
                ROUND(SUM(f.line_total), 2) AS total_revenue,
                ROUND(AVG(f.line_total), 2) AS avg_item_revenue
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            GROUP BY d.year_month, d.year, d.month_name;
            """))

            conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_revenue_by_product AS
            SELECT 
                p.stock_code,
                p.description,
                COUNT(DISTINCT f.invoice_no) AS orders_count,
                SUM(f.quantity) AS total_units_sold,
                ROUND(SUM(f.line_total), 2) AS total_revenue,
                ROUND(AVG(f.unit_price), 2) AS avg_price
            FROM fact_sales f
            JOIN dim_product p ON f.stock_code = p.stock_code
            GROUP BY p.stock_code, p.description;
            """))

            conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_revenue_by_country AS
            SELECT 
                f.country,
                COUNT(DISTINCT f.invoice_no) AS total_orders,
                COUNT(DISTINCT f.customer_id) AS total_customers,
                SUM(f.quantity) AS total_units_sold,
                ROUND(SUM(f.line_total), 2) AS total_revenue,
                ROUND(SUM(f.line_total) / MAX(1, COUNT(DISTINCT f.invoice_no)), 2) AS avg_order_value
            FROM fact_sales f
            GROUP BY f.country;
            """))

            conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_product_demand_trends AS
            SELECT 
                f.stock_code,
                p.description,
                d.year_month,
                SUM(f.quantity) AS monthly_units_sold,
                ROUND(SUM(f.line_total), 2) AS monthly_revenue
            FROM fact_sales f
            JOIN dim_product p ON f.stock_code = p.stock_code
            JOIN dim_date d ON f.date_key = d.date_key
            GROUP BY f.stock_code, p.description, d.year_month;
            """))

            conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_customer_purchase_frequency AS
            SELECT 
                customer_id,
                country,
                COUNT(DISTINCT invoice_no) AS total_purchases,
                ROUND(SUM(line_total), 2) AS total_spend,
                ROUND(AVG(line_total), 2) AS avg_line_value,
                MIN(invoice_date) AS first_purchase_date,
                MAX(invoice_date) AS last_purchase_date
            FROM fact_sales
            WHERE customer_id IS NOT NULL AND is_guest = 0
            GROUP BY customer_id, country;
            """))

            conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_average_order_value AS
            SELECT 
                d.year_month,
                COUNT(DISTINCT f.invoice_no) AS total_orders,
                ROUND(SUM(f.line_total), 2) AS gross_revenue,
                ROUND(SUM(f.line_total) / MAX(1, COUNT(DISTINCT f.invoice_no)), 2) AS average_order_value
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            GROUP BY d.year_month;
            """))

            conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_top_performing_products AS
            SELECT 
                p.stock_code,
                p.description,
                ROUND(SUM(f.line_total), 2) AS total_revenue,
                SUM(f.quantity) AS total_units,
                DENSE_RANK() OVER (ORDER BY SUM(f.line_total) DESC) AS revenue_rank
            FROM fact_sales f
            JOIN dim_product p ON f.stock_code = p.stock_code
            GROUP BY p.stock_code, p.description;
            """))
        except Exception as e:
            # Views might already exist or dialect variation
            pass


def init_db():
    """Create all tables in the configured database and setup views."""
    # Import entities so they register with Base.metadata
    from backend.app.models.entities import (
        DimDate, DimProduct, DimCustomer, FactSale,
        DailySale, MonthlySale, ProductMetric, CustomerMetric,
        ForecastResult, InventoryParameter, PipelineRun,
        DataQualityReport, RawTransaction
    )
    Base.metadata.create_all(bind=engine)
    create_views_if_needed()
