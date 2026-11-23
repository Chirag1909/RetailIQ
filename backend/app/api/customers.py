"""
RetailIQ - Customer Analytics & RFM Endpoints (backend/app/api/customers.py)
Provides customer segmentation, RFM scorecards, and historical revenue distribution.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd
from backend.app.database.session import get_db
from backend.app.schemas.schemas import (
    CustomerSummaryResponse, CustomerSegmentItem, CustomerRFMItem
)
from backend.app.analytics.rfm import CustomerRFMAnalyzer

router = APIRouter(prefix="/customers", tags=["Customer Analytics"])


@router.get("/summary", response_model=CustomerSummaryResponse)
def get_customer_summary(db: Session = Depends(get_db)):
    """Computes comprehensive RFM segmentation summary across all identified accounts."""
    df_cust = pd.read_sql(text("""
        SELECT customer_id, country, order_count, total_spend, total_units, recency_days
        FROM customer_metrics;
    """), db.bind)

    rfm_results = CustomerRFMAnalyzer.analyze_rfm(df_cust)
    summary = rfm_results["summary"]
    segments = [
        CustomerSegmentItem(**seg) for seg in rfm_results["segment_distribution"]
    ]

    return CustomerSummaryResponse(
        total_identified_customers=summary["total_identified_customers"],
        total_historical_spend=summary["total_historical_spend"],
        avg_customer_lifetime_spend=summary["avg_customer_lifetime_spend"],
        repeat_customer_count=summary["repeat_customer_count"],
        repeat_customer_rate_pct=summary["repeat_customer_rate_pct"],
        segments=segments
    )


@router.get("/segments", response_model=List[CustomerSegmentItem])
def get_customer_segments(db: Session = Depends(get_db)):
    """Returns list of RFM segments, descriptions, and revenue share."""
    df_cust = pd.read_sql(text("""
        SELECT customer_id, country, order_count, total_spend, total_units, recency_days
        FROM customer_metrics;
    """), db.bind)

    rfm_results = CustomerRFMAnalyzer.analyze_rfm(df_cust)
    return [
        CustomerSegmentItem(**seg) for seg in rfm_results["segment_distribution"]
    ]


@router.get("/rfm", response_model=List[CustomerRFMItem])
def get_customer_rfm_records(
    limit: int = Query(50, ge=1, le=200),
    segment: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns top customer accounts with individual RFM metrics."""
    df_cust = pd.read_sql(text("""
        SELECT customer_id, country, order_count, total_spend, total_units, recency_days, avg_order_value
        FROM customer_metrics;
    """), db.bind)

    rfm_results = CustomerRFMAnalyzer.analyze_rfm(df_cust)
    df_scored = rfm_results["segmented_df"]

    if segment and segment != "ALL":
        df_scored = df_scored[df_scored["segment"] == segment]

    if search:
        df_scored = df_scored[df_scored["customer_id"].str.contains(search, case=False, na=False)]

    df_scored = df_scored.sort_values("total_spend", ascending=False).head(limit)

    return [
        CustomerRFMItem(
            customer_id=row["customer_id"],
            country=row["country"],
            total_spend=float(row["total_spend"]),
            order_count=int(row["order_count"]),
            recency_days=int(row["recency_days"]),
            avg_order_value=float(row["avg_order_value"]),
            segment=row["segment"]
        )
        for _, row in df_scored.iterrows()
    ]
