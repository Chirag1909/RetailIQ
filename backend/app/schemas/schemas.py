"""
RetailIQ - Pydantic Request & Response Schemas (backend/app/schemas/schemas.py)
Type-safe request validation and response serialization across all endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


# Health & Metadata
class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    timestamp: str
    environment: str = "production"


class MetadataResponse(BaseModel):
    project_name: str
    version: str
    description: str
    dataset_source: str
    supported_models: List[str]
    forecast_horizons: List[int]


# Dashboard
class DashboardSummaryResponse(BaseModel):
    total_revenue: float
    total_orders: int
    units_sold: int
    average_order_value: float
    unique_customers: int
    repeat_customer_rate: float
    active_products: int
    monitored_countries: int
    quality_score: float


class RevenueTrendItem(BaseModel):
    date: str
    revenue: float
    orders: int
    quantity: int


class TopProductItem(BaseModel):
    stock_code: str
    description: str
    total_revenue: float
    total_quantity: int
    revenue_rank: Optional[int] = None


class CountryPerformanceItem(BaseModel):
    country: str
    total_revenue: float
    total_orders: int
    total_customers: int
    avg_order_value: float
    global_share_pct: float


# Sales
class SaleRecordItem(BaseModel):
    sale_id: int
    invoice_no: str
    stock_code: str
    customer_id: Optional[str]
    invoice_date: str
    quantity: int
    unit_price: float
    line_total: float
    country: str
    is_guest: int


class SalesPaginatedResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    data: List[SaleRecordItem]


class MonthlySaleItem(BaseModel):
    year_month: str
    revenue: float
    orders: int
    quantity: int
    unique_customers: int
    mom_growth_pct: float


class ProductSummaryItem(BaseModel):
    stock_code: str
    description: str
    total_revenue: float
    total_quantity: int
    order_count: int
    avg_unit_price: float
    revenue_rank: Optional[int]
    demand_velocity_category: Optional[str]


# Customer Analytics & RFM
class CustomerSegmentItem(BaseModel):
    segment: str
    customer_count: int
    customer_pct: float
    total_spend: float
    spend_pct: float
    avg_recency_days: float
    avg_frequency: float
    avg_monetary: float
    description: str


class CustomerSummaryResponse(BaseModel):
    total_identified_customers: int
    total_historical_spend: float
    avg_customer_lifetime_spend: float
    repeat_customer_count: int
    repeat_customer_rate_pct: float
    segments: List[CustomerSegmentItem]


class CustomerRFMItem(BaseModel):
    customer_id: str
    country: str
    total_spend: float
    order_count: int
    recency_days: int
    avg_order_value: float
    segment: Optional[str]


# Forecast
class ForecastPoint(BaseModel):
    forecast_date: str
    predicted_value: float
    lower_bound: Optional[float]
    upper_bound: Optional[float]


class ForecastResponse(BaseModel):
    target_type: str
    target_identifier: str
    horizon_days: int
    model_name: str
    mae: Optional[float]
    rmse: Optional[float]
    mape: Optional[float]
    wape: Optional[float]
    trained_at: str
    forecasts: List[ForecastPoint]
    historical_baseline: Optional[List[Dict[str, Any]]] = None


class ForecastModelLeaderboardItem(BaseModel):
    model_name: str
    mae: float
    rmse: float
    mape: float
    wape: float
    is_champion: bool


class ForecastAccuracyResponse(BaseModel):
    target_identifier: str
    leaderboard: List[ForecastModelLeaderboardItem]


# Inventory
class InventoryItem(BaseModel):
    stock_code: str
    description: str
    current_stock: int
    lead_time_days: int
    service_level_pct: float
    expected_lead_time_demand: float
    safety_stock: int
    reorder_point: int
    suggested_reorder_qty: int
    inventory_coverage_days: float
    stockout_risk_level: str
    overstock_risk_level: str
    action_recommendation: Optional[str] = None


class InventoryOverviewResponse(BaseModel):
    total_monitored_skus: int
    critical_stockout_count: int
    high_stockout_count: int
    overstock_risk_count: int
    average_coverage_days: float
    inventory_items: List[InventoryItem]


class InventoryParamUpdateRequest(BaseModel):
    current_stock: Optional[int] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=1)
    service_level_pct: Optional[float] = Field(None, ge=80.0, le=99.9)
    holding_cost: Optional[float] = Field(None, ge=0.01)
    reorder_cost: Optional[float] = Field(None, ge=1.0)


# Pipeline
class PipelineRunItem(BaseModel):
    run_id: str
    pipeline_name: str
    status: str
    started_at: str
    completed_at: Optional[str]
    records_extracted: int
    records_cleaned: int
    records_loaded: int
    data_quality_score: Optional[float]
    execution_duration_sec: Optional[float]
    error_message: Optional[str]
    triggered_by: str


class PipelineStatusResponse(BaseModel):
    latest_run: Optional[PipelineRunItem]
    total_runs: int
    system_health: str
    last_quality_score: float
