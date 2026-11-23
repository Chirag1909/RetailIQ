"""
RetailIQ - Sales Analytics Endpoints (backend/app/api/sales.py)
Provides paginated transaction queries, monthly aggregates, and SKU-level drilldowns.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import (
    SalesPaginatedResponse, SaleRecordItem, MonthlySaleItem, ProductSummaryItem
)

router = APIRouter(prefix="/sales", tags=["Sales Analytics"])


@router.get("", response_model=SalesPaginatedResponse)
def get_sales_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    country: Optional[str] = Query(None),
    stock_code: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns paginated fact_sales transactions with dynamic filtering."""
    base_query = "FROM fact_sales WHERE 1=1"
    params = {}

    if country and country != "ALL":
        base_query += " AND country = :country"
        params["country"] = country

    if stock_code:
        base_query += " AND stock_code = :stock_code"
        params["stock_code"] = stock_code

    if search:
        base_query += " AND (invoice_no LIKE :search OR stock_code LIKE :search)"
        params["search"] = f"%{search}%"

    # Count total matching
    count_sql = f"SELECT COUNT(*) {base_query};"
    total_count = db.execute(text(count_sql), params).scalar() or 0

    # Fetch page
    offset = (page - 1) * page_size
    data_sql = f"""
        SELECT sale_id, invoice_no, stock_code, customer_id, invoice_date, quantity, unit_price, line_total, country, is_guest
        {base_query}
        ORDER BY invoice_date DESC
        LIMIT :limit OFFSET :offset;
    """
    params["limit"] = page_size
    params["offset"] = offset

    rows = db.execute(text(data_sql), params).fetchall()

    items = [
        SaleRecordItem(
            sale_id=row[0],
            invoice_no=row[1],
            stock_code=row[2],
            customer_id=row[3],
            invoice_date=str(row[4]),
            quantity=int(row[5]),
            unit_price=float(row[6]),
            line_total=float(row[7]),
            country=row[8],
            is_guest=int(row[9])
        )
        for row in rows
    ]

    total_pages = max(1, (total_count + page_size - 1) // page_size)
    return SalesPaginatedResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        data=items
    )


@router.get("/monthly", response_model=List[MonthlySaleItem])
def get_monthly_sales(db: Session = Depends(get_db)):
    """Returns monthly performance aggregates and month-over-month growth rate."""
    rows = db.execute(text("""
        SELECT year_month, revenue, order_count, quantity_sold, unique_customers, mom_growth_pct
        FROM monthly_sales
        ORDER BY year_month ASC;
    """)).fetchall()

    return [
        MonthlySaleItem(
            year_month=row[0],
            revenue=float(row[1]),
            orders=int(row[2]),
            quantity=int(row[3]),
            unique_customers=int(row[4]),
            mom_growth_pct=float(row[5] or 0.0)
        )
        for row in rows
    ]


@router.get("/products", response_model=List[ProductSummaryItem])
def get_product_metrics(
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    velocity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns product performance summaries and demand velocity rankings."""
    query = "SELECT stock_code, description, total_revenue, total_quantity, order_count, avg_unit_price, revenue_rank, demand_velocity_category FROM product_metrics WHERE 1=1"
    params = {"limit": limit}

    if search:
        query += " AND (stock_code LIKE :search OR description LIKE :search)"
        params["search"] = f"%{search}%"

    if velocity and velocity != "ALL":
        query += " AND demand_velocity_category = :velocity"
        params["velocity"] = velocity

    query += " ORDER BY total_revenue DESC LIMIT :limit;"
    rows = db.execute(text(query), params).fetchall()

    return [
        ProductSummaryItem(
            stock_code=row[0],
            description=row[1],
            total_revenue=float(row[2]),
            total_quantity=int(row[3]),
            order_count=int(row[4]),
            avg_unit_price=float(row[5]),
            revenue_rank=row[6],
            demand_velocity_category=row[7]
        )
        for row in rows
    ]
