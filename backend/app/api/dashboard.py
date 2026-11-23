"""
RetailIQ - Executive Dashboard Endpoints (backend/app/api/dashboard.py)
Delivers real high-level KPIs, revenue time-series trajectories, and geographic performance.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import (
    DashboardSummaryResponse, RevenueTrendItem, TopProductItem, CountryPerformanceItem
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Computes genuine executive KPIs from the analytical database."""
    # Aggregates from daily_sales
    kpi_res = db.execute(text("""
        SELECT 
            COALESCE(SUM(revenue), 0.0) as total_revenue,
            COALESCE(SUM(order_count), 0) as total_orders,
            COALESCE(SUM(quantity_sold), 0) as total_units
        FROM daily_sales;
    """)).fetchone()

    total_rev = float(kpi_res[0])
    total_orders = int(kpi_res[1])
    total_units = int(kpi_res[2])
    aov = round(total_rev / max(1, total_orders), 2)

    # Customer metrics
    cust_res = db.execute(text("""
        SELECT 
            COUNT(*) as unique_customers,
            COALESCE(SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END), 0) as repeat_customers
        FROM customer_metrics;
    """)).fetchone()

    unique_cust = int(cust_res[0]) if cust_res else 0
    repeat_cust = int(cust_res[1]) if cust_res else 0
    repeat_rate = round((repeat_cust / max(1, unique_cust)) * 100, 2)

    # Product and country counts
    prod_count = db.execute(text("SELECT COUNT(*) FROM dim_product;")).scalar() or 0
    country_count = db.execute(text("SELECT COUNT(DISTINCT country) FROM dim_customer;")).scalar() or 0

    # Data quality score
    quality_score = db.execute(text("""
        SELECT data_quality_score 
        FROM pipeline_runs 
        WHERE status = 'SUCCESS' 
        ORDER BY started_at DESC LIMIT 1;
    """)).scalar() or 95.0

    return DashboardSummaryResponse(
        total_revenue=round(total_rev, 2),
        total_orders=total_orders,
        units_sold=total_units,
        average_order_value=aov,
        unique_customers=unique_cust,
        repeat_customer_rate=repeat_rate,
        active_products=prod_count,
        monitored_countries=country_count,
        quality_score=float(quality_score)
    )


@router.get("/revenue-trend", response_model=List[RevenueTrendItem])
def get_revenue_trend(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Returns chronological daily sales trends for interactive charts."""
    query_str = "SELECT date_key, revenue, order_count, quantity_sold FROM daily_sales"
    params = {}
    conditions = []

    if start_date:
        conditions.append("date_key >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("date_key <= :end_date")
        params["end_date"] = end_date

    if conditions:
        query_str += " WHERE " + " AND ".join(conditions)

    query_str += " ORDER BY date_key ASC;"
    rows = db.execute(text(query_str), params).fetchall()

    return [
        RevenueTrendItem(
            date=str(row[0]),
            revenue=float(row[1]),
            orders=int(row[2]),
            quantity=int(row[3])
        )
        for row in rows
    ]


@router.get("/top-products", response_model=List[TopProductItem])
def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Returns top merchandise products ranked by total revenue."""
    rows = db.execute(text("""
        SELECT stock_code, description, total_revenue, total_quantity, revenue_rank
        FROM product_metrics
        ORDER BY total_revenue DESC
        LIMIT :limit;
    """), {"limit": limit}).fetchall()

    return [
        TopProductItem(
            stock_code=row[0],
            description=row[1],
            total_revenue=float(row[2]),
            total_quantity=int(row[3]),
            revenue_rank=row[4]
        )
        for row in rows
    ]


@router.get("/country-performance", response_model=List[CountryPerformanceItem])
def get_country_performance(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Returns country revenue distribution and percentage contribution."""
    total_rev = db.execute(text("SELECT SUM(total_spend) FROM customer_metrics;")).scalar() or 1.0

    rows = db.execute(text("""
        SELECT 
            country,
            COALESCE(SUM(total_spend), 0.0) as rev,
            COALESCE(SUM(order_count), 0) as orders,
            COUNT(customer_id) as customers
        FROM customer_metrics
        GROUP BY country
        ORDER BY rev DESC
        LIMIT :limit;
    """), {"limit": limit}).fetchall()

    result = []
    for r in rows:
        c_rev = float(r[1])
        c_orders = int(r[2])
        c_cust = int(r[3])
        result.append(CountryPerformanceItem(
            country=r[0],
            total_revenue=round(c_rev, 2),
            total_orders=c_orders,
            total_customers=c_cust,
            avg_order_value=round(c_rev / max(1, c_orders), 2),
            global_share_pct=round((c_rev / total_rev) * 100, 2)
        ))
    return result
