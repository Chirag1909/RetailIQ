"""
RetailIQ - Demand Forecasting Endpoints (backend/app/api/forecast.py)
Delivers genuine multi-horizon predictions, confidence intervals, and model leaderboards.
"""

import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd
from backend.app.database.session import get_db
from backend.app.schemas.schemas import (
    ForecastResponse, ForecastPoint, ForecastAccuracyResponse, ForecastModelLeaderboardItem
)

router = APIRouter(prefix="/forecast", tags=["Demand Forecasting"])


@router.get("", response_model=ForecastResponse)
def get_forecast(
    target_type: str = Query("GLOBAL_REVENUE", description="GLOBAL_REVENUE or PRODUCT_DEMAND"),
    target_identifier: str = Query("ALL", description="ALL for global, or StockCode e.g. 22423"),
    horizon_days: int = Query(30, description="7, 30, or 90"),
    db: Session = Depends(get_db)
):
    """
    Returns forecasted demand or daily revenue with statistical confidence intervals.
    """
    # Fetch forecast records from DB
    rows = db.execute(text("""
        SELECT forecast_date, predicted_value, lower_bound, upper_bound, model_name, mae, rmse, mape, wape, trained_at
        FROM forecast_results
        WHERE target_type = :ttype 
          AND target_identifier = :tid 
          AND horizon_days = :h
        ORDER BY forecast_date ASC;
    """), {
        "ttype": target_type,
        "tid": target_identifier,
        "h": horizon_days
    }).fetchall()

    if not rows:
        # Check if any forecasts exist for this target
        any_rows = db.execute(text("""
            SELECT horizon_days FROM forecast_results WHERE target_identifier = :tid LIMIT 1;
        """), {"tid": target_identifier}).fetchall()
        if not any_rows:
            raise HTTPException(
                status_code=404,
                detail=f"No forecast model trained for target '{target_identifier}'. Supported targets include 'ALL' (global revenue) and top SKUs: 22423, 85123A, 85099B, 47566."
            )

    points = [
        ForecastPoint(
            forecast_date=str(row[0]),
            predicted_value=float(row[1]),
            lower_bound=float(row[2]) if row[2] is not None else None,
            upper_bound=float(row[3]) if row[3] is not None else None
        )
        for row in rows
    ]

    first_row = rows[0]
    model_name = first_row[4]
    mae = float(first_row[5]) if first_row[5] is not None else None
    rmse = float(first_row[6]) if first_row[6] is not None else None
    mape = float(first_row[7]) if first_row[7] is not None else None
    wape = float(first_row[8]) if first_row[8] is not None else None
    trained_at = str(first_row[9])

    # Fetch recent historical baseline for actual vs predicted charts
    history = []
    if target_type == "GLOBAL_REVENUE":
        hist_rows = db.execute(text("""
            SELECT date_key, revenue 
            FROM daily_sales 
            ORDER BY date_key DESC LIMIT 60;
        """)).fetchall()
        for hr in reversed(hist_rows):
            history.append({"date": str(hr[0]), "actual": float(hr[1])})
    else:
        hist_rows = db.execute(text("""
            SELECT date_key, SUM(quantity) as qty
            FROM fact_sales
            WHERE stock_code = :sku
            GROUP BY date_key
            ORDER BY date_key DESC LIMIT 60;
        """), {"sku": target_identifier}).fetchall()
        for hr in reversed(hist_rows):
            history.append({"date": str(hr[0]), "actual": float(hr[1])})

    return ForecastResponse(
        target_type=target_type,
        target_identifier=target_identifier,
        horizon_days=horizon_days,
        model_name=model_name,
        mae=mae,
        rmse=rmse,
        mape=mape,
        wape=wape,
        trained_at=trained_at,
        forecasts=points,
        historical_baseline=history
    )


@router.get("/accuracy", response_model=ForecastAccuracyResponse)
def get_forecast_accuracy(
    target_identifier: str = Query("ALL", description="ALL or StockCode"),
    db: Session = Depends(get_db)
):
    """
    Returns competitive evaluation leaderboard comparing all 3 candidate models.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    target_key = target_identifier.lower().replace(" ", "_")
    meta_files = list((base_dir / "ml" / "models").glob(f"*_{target_key}_meta.json"))

    if not meta_files:
        # Fallback to querying DB distinct models
        rows = db.execute(text("""
            SELECT DISTINCT model_name, mae, rmse, mape, wape
            FROM forecast_results
            WHERE target_identifier = :tid;
        """), {"tid": target_identifier}).fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail=f"No accuracy metrics found for {target_identifier}")

        leaderboard = [
            ForecastModelLeaderboardItem(
                model_name=r[0],
                mae=float(r[1] or 0.0),
                rmse=float(r[2] or 0.0),
                mape=float(r[3] or 0.0),
                wape=float(r[4] or 0.0),
                is_champion=True
            )
            for r in rows
        ]
        return ForecastAccuracyResponse(target_identifier=target_identifier, leaderboard=leaderboard)

    with open(meta_files[0], "r", encoding="utf-8") as f:
        meta = json.load(f)

    champ_name = meta.get("champion_model", "")
    items = []
    for m in meta.get("leaderboard", []):
        m_name = m["name"]
        metrics = m["metrics"]
        items.append(ForecastModelLeaderboardItem(
            model_name=m_name,
            mae=metrics["mae"],
            rmse=metrics["rmse"],
            mape=metrics["mape"],
            wape=metrics["wape"],
            is_champion=(m_name == champ_name)
        ))

    return ForecastAccuracyResponse(target_identifier=target_identifier, leaderboard=items)


@router.get("/models")
def get_available_models(db: Session = Depends(get_db)):
    """Lists distinct trained forecast targets and model artifacts."""
    targets = db.execute(text("""
        SELECT DISTINCT target_type, target_identifier, model_name, trained_at
        FROM forecast_results
        ORDER BY target_identifier ASC;
    """)).fetchall()

    return [
        {
            "target_type": r[0],
            "target_identifier": r[1],
            "champion_model": r[2],
            "trained_at": str(r[3])
        }
        for r in targets
    ]
