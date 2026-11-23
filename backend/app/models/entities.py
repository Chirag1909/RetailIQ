"""
RetailIQ - SQLAlchemy ORM Entity Models (backend/app/models/entities.py)
Defines Star-Schema Dimensions, Facts, Aggregate Tables, and Operational Entities.
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Text, Date, DateTime, Numeric, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


class RawTransaction(Base):
    __tablename__ = "raw_transactions"

    raw_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    invoice_no = Column(String(64), nullable=False, index=True)
    stock_code = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=True)
    invoice_date = Column(DateTime, nullable=True, index=True)
    unit_price = Column(Numeric(12, 4), nullable=True)
    customer_id = Column(String(64), nullable=True)
    country = Column(String(100), nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)


class DimDate(Base):
    __tablename__ = "dim_date"

    date_key = Column(Date, primary_key=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String(20), nullable=False)
    year_month = Column(String(7), nullable=False, index=True)
    day_of_month = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    day_name = Column(String(20), nullable=False)
    is_weekend = Column(Integer, default=0, nullable=False)
    quarter_name = Column(String(10), nullable=False)

    sales = relationship("FactSale", back_populates="date_dim")


class DimProduct(Base):
    __tablename__ = "dim_product"

    stock_code = Column(String(64), primary_key=True)
    description = Column(Text, nullable=False, index=True)
    avg_unit_price = Column(Numeric(12, 2), default=0.0, nullable=False)
    total_lifetime_revenue = Column(Numeric(14, 2), default=0.0, nullable=False)
    total_lifetime_quantity = Column(BigInteger, default=0, nullable=False)
    first_sold_date = Column(DateTime, nullable=True)
    last_sold_date = Column(DateTime, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sales = relationship("FactSale", back_populates="product_dim")
    inventory = relationship("InventoryParameter", back_populates="product_dim", uselist=False)
    metrics = relationship("ProductMetric", back_populates="product_dim", uselist=False)


class DimCustomer(Base):
    __tablename__ = "dim_customer"

    customer_id = Column(String(64), primary_key=True)
    country = Column(String(100), nullable=False, index=True)
    first_order_date = Column(DateTime, nullable=True)
    last_order_date = Column(DateTime, nullable=True)
    total_orders = Column(Integer, default=0, nullable=False)
    total_spend = Column(Numeric(14, 2), default=0.0, nullable=False)
    rfm_recency = Column(Integer, nullable=True)
    rfm_frequency = Column(Integer, nullable=True)
    rfm_monetary = Column(Numeric(14, 2), nullable=True)
    rfm_segment = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FactSale(Base):
    __tablename__ = "fact_sales"

    sale_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    invoice_no = Column(String(64), nullable=False, index=True)
    stock_code = Column(String(64), ForeignKey("dim_product.stock_code"), nullable=False, index=True)
    customer_id = Column(String(64), nullable=True, index=True)
    date_key = Column(Date, ForeignKey("dim_date.date_key"), nullable=False, index=True)
    invoice_date = Column(DateTime, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 4), nullable=False)
    line_total = Column(Numeric(14, 2), nullable=False)
    country = Column(String(100), nullable=False, index=True)
    is_guest = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    product_dim = relationship("DimProduct", back_populates="sales")
    date_dim = relationship("DimDate", back_populates="sales")


class DailySale(Base):
    __tablename__ = "daily_sales"

    date_key = Column(Date, primary_key=True)
    revenue = Column(Numeric(14, 2), nullable=False)
    order_count = Column(Integer, nullable=False)
    quantity_sold = Column(BigInteger, nullable=False)
    unique_customers = Column(Integer, nullable=False)
    avg_order_value = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class MonthlySale(Base):
    __tablename__ = "monthly_sales"

    year_month = Column(String(7), primary_key=True)
    revenue = Column(Numeric(14, 2), nullable=False)
    order_count = Column(Integer, nullable=False)
    quantity_sold = Column(BigInteger, nullable=False)
    unique_customers = Column(Integer, nullable=False)
    mom_growth_pct = Column(Numeric(8, 2), default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProductMetric(Base):
    __tablename__ = "product_metrics"

    stock_code = Column(String(64), ForeignKey("dim_product.stock_code"), primary_key=True)
    description = Column(Text, nullable=False)
    total_revenue = Column(Numeric(14, 2), nullable=False, index=True)
    total_quantity = Column(BigInteger, nullable=False)
    order_count = Column(Integer, nullable=False)
    avg_unit_price = Column(Numeric(12, 2), nullable=False)
    revenue_rank = Column(Integer, nullable=True)
    demand_velocity_category = Column(String(32), nullable=True)
    first_sold_date = Column(DateTime, nullable=True)
    last_sold_date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product_dim = relationship("DimProduct", back_populates="metrics")


class CustomerMetric(Base):
    __tablename__ = "customer_metrics"

    customer_id = Column(String(64), primary_key=True)
    country = Column(String(100), nullable=False)
    first_order_date = Column(DateTime, nullable=True)
    last_order_date = Column(DateTime, nullable=True)
    order_count = Column(Integer, nullable=False)
    total_spend = Column(Numeric(14, 2), nullable=False, index=True)
    total_units = Column(BigInteger, nullable=False)
    avg_order_value = Column(Numeric(12, 2), nullable=False)
    recency_days = Column(Integer, nullable=False)
    rfm_score = Column(String(10), nullable=True)
    segment = Column(String(50), nullable=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    forecast_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    target_type = Column(String(32), nullable=False) # 'GLOBAL_REVENUE' or 'PRODUCT_DEMAND'
    target_identifier = Column(String(64), nullable=False) # 'ALL' or stock_code
    model_name = Column(String(64), nullable=False)
    horizon_days = Column(Integer, nullable=False) # 7, 30, 90
    forecast_date = Column(Date, nullable=False, index=True)
    predicted_value = Column(Numeric(14, 2), nullable=False)
    lower_bound = Column(Numeric(14, 2), nullable=True)
    upper_bound = Column(Numeric(14, 2), nullable=True)
    mae = Column(Numeric(12, 4), nullable=True)
    rmse = Column(Numeric(12, 4), nullable=True)
    mape = Column(Numeric(8, 4), nullable=True)
    wape = Column(Numeric(8, 4), nullable=True)
    trained_at = Column(DateTime, default=datetime.utcnow)


class InventoryParameter(Base):
    __tablename__ = "inventory_parameters"

    stock_code = Column(String(64), ForeignKey("dim_product.stock_code"), primary_key=True)
    current_stock = Column(Integer, default=100, nullable=False)
    lead_time_days = Column(Integer, default=14, nullable=False)
    service_level_pct = Column(Numeric(5, 2), default=95.0, nullable=False)
    holding_cost = Column(Numeric(8, 2), default=1.50, nullable=False)
    reorder_cost = Column(Numeric(8, 2), default=25.00, nullable=False)
    expected_lead_time_demand = Column(Numeric(10, 2), default=0.0, nullable=False)
    safety_stock = Column(Integer, default=0, nullable=False)
    reorder_point = Column(Integer, default=0, nullable=False)
    suggested_reorder_qty = Column(Integer, default=0, nullable=False)
    inventory_coverage_days = Column(Numeric(8, 1), default=0.0, nullable=False)
    stockout_risk_level = Column(String(20), default="Low", nullable=False)
    overstock_risk_level = Column(String(20), default="Low", nullable=False)
    last_evaluated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product_dim = relationship("DimProduct", back_populates="inventory")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    run_id = Column(String(64), primary_key=True)
    pipeline_name = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False) # 'SUCCESS', 'FAILED', 'RUNNING'
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    records_extracted = Column(Integer, default=0)
    records_cleaned = Column(Integer, default=0)
    records_loaded = Column(Integer, default=0)
    data_quality_score = Column(Numeric(5, 2), nullable=True)
    execution_duration_sec = Column(Numeric(10, 2), nullable=True)
    error_message = Column(Text, nullable=True)
    triggered_by = Column(String(64), default="SYSTEM")


class DataQualityReport(Base):
    __tablename__ = "data_quality_reports"

    report_id = Column(String(64), primary_key=True)
    generated_at = Column(DateTime, nullable=False)
    overall_quality_score = Column(Numeric(5, 2), nullable=False)
    status = Column(String(32), nullable=False)
    raw_record_count = Column(Integer, nullable=False)
    cleaned_record_count = Column(Integer, nullable=False)
    retention_rate_pct = Column(Numeric(5, 2), nullable=False)
    duplicate_records = Column(Integer, nullable=False)
    missing_customer_ids = Column(Integer, nullable=False)
    cancellations_detected = Column(Integer, nullable=False)
    report_json = Column(Text, nullable=False)
