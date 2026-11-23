"""
RetailIQ - Time-Series Model Training, Evaluation, and Forecast Pipeline (ml/training/trainer.py)
Orchestrates model training across Seasonal Naive, Exponential Smoothing, and XGBoost.
Evaluates on chronological test set, compares leaderboard, serializes champion model,
and persists multi-horizon (7, 30, 90 day) predictions to the database.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import joblib
import numpy as np
import pandas as pd
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.database.session import engine, SessionLocal
from backend.app.models.entities import ForecastResult
from ml.features.builder import prepare_time_series_frame, build_forecasting_features, chronological_train_test_split
from ml.evaluation.metrics import compute_metrics
from ml.training.models import SeasonalNaiveModel, StatisticalExpSmoothingModel, XGBoostForecaster

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RetailIQ-Trainer")


class ForecastPipelineManager:
    """Manages model lifecycle, competitive evaluation, and forecast persistence."""

    def __init__(self):
        self.models_dir = BASE_DIR / "ml" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def train_and_forecast_series(
        self,
        target_type: str,
        target_identifier: str,
        raw_series_df: pd.DataFrame,
        date_col: str = "date_key",
        val_col: str = "revenue"
    ) -> Dict[str, Any]:
        """
        Executes end-to-end forecasting workflow for a given series.
        """
        logger.info(f"--- Training Forecast Engine: [{target_type}] identifier={target_identifier} ---")

        # 1. Prepare continuous time series
        ts_df = prepare_time_series_frame(raw_series_df, date_col=date_col, value_col=val_col)
        if len(ts_df) < 60:
            logger.warning(f"History too short ({len(ts_df)} days) for {target_identifier}. Minimum 60 days required.")
            return {"status": "INSUFFICIENT_HISTORY", "points": len(ts_df)}

        # 2. Build feature matrix
        feat_df = build_forecasting_features(ts_df)

        # 3. Chronological Train-Test Split (last 30 days as out-of-time evaluation test)
        eval_horizon = 30
        train_df, test_df = chronological_train_test_split(feat_df, test_horizon_days=eval_horizon)
        y_test = test_df["y"].values

        # 4. Train Model 1: Seasonal Naive
        logger.info("Fitting Model 1: Seasonal Naive Baseline...")
        m_snaive = SeasonalNaiveModel(season_length=7)
        m_snaive.fit(train_df["y"].values)
        pred_snaive = m_snaive.predict(steps=eval_horizon)
        eval_snaive = compute_metrics(y_test, pred_snaive)

        # 5. Train Model 2: Holt-Winters Exponential Smoothing
        logger.info("Fitting Model 2: Holt-Winters Exponential Smoothing...")
        m_expsmooth = StatisticalExpSmoothingModel(seasonal_periods=7)
        m_expsmooth.fit(train_df["y"].values)
        pred_expsmooth = m_expsmooth.predict(steps=eval_horizon)
        eval_expsmooth = compute_metrics(y_test, pred_expsmooth)

        # 6. Train Model 3: XGBoost ML Forecaster
        logger.info("Fitting Model 3: XGBoost Regressor with Lags & Rolling Features...")
        m_xgb = XGBoostForecaster()
        m_xgb.fit(train_df)
        pred_xgb = m_xgb.predict_features(test_df)
        eval_xgb = compute_metrics(y_test, pred_xgb)

        leaderboard = [
            {"model_name": "Seasonal Naive Baseline", "metrics": eval_snaive, "model_obj": m_snaive},
            {"model_name": "Holt-Winters Exponential Smoothing", "metrics": eval_expsmooth, "model_obj": m_expsmooth},
            {"model_name": "XGBoost Regressor", "metrics": eval_xgb, "model_obj": m_xgb}
        ]

        # Sort by WAPE ascending (lowest error wins)
        leaderboard.sort(key=lambda x: x["metrics"]["wape"])
        champion = leaderboard[0]
        logger.info(f"Leaderboard Champion for {target_identifier}: {champion['model_name']} (WAPE: {champion['metrics']['wape']}%, RMSE: {champion['metrics']['rmse']})")

        # 7. Generate Multi-Horizon Forecasts (7, 30, 90 days) using full history
        # Retrain champion XGBoost on entire dataset for maximum signal
        champion_xgb = XGBoostForecaster()
        champion_xgb.fit(feat_df)

        db = SessionLocal()
        persisted_records = []

        # Residual stddev for confidence interval bounds
        residual_std = champion["metrics"]["rmse"]

        for horizon in [7, 30, 90]:
            future_dates, future_preds = champion_xgb.recursive_forecast(ts_df, horizon_days=horizon)
            for d, pred_val in zip(future_dates, future_preds):
                low_b = max(0.0, float(pred_val - 1.96 * residual_std))
                upp_b = float(pred_val + 1.96 * residual_std)

                entry = ForecastResult(
                    target_type=target_type,
                    target_identifier=str(target_identifier),
                    model_name=champion["model_name"],
                    horizon_days=horizon,
                    forecast_date=d.date(),
                    predicted_value=round(float(pred_val), 2),
                    lower_bound=round(low_b, 2),
                    upper_bound=round(upp_b, 2),
                    mae=champion["metrics"]["mae"],
                    rmse=champion["metrics"]["rmse"],
                    mape=champion["metrics"]["mape"],
                    wape=champion["metrics"]["wape"],
                    trained_at=datetime.utcnow()
                )
                db.add(entry)
                persisted_records.append(entry)

        db.commit()
        db.close()

        # 8. Serialize Champion Artifact
        artifact_path = self.models_dir / f"model_{target_type.lower()}_{target_identifier.lower().replace(' ', '_')}.joblib"
        meta_path = self.models_dir / f"model_{target_type.lower()}_{target_identifier.lower().replace(' ', '_')}_meta.json"

        joblib.dump(champion_xgb.model, artifact_path)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "target_type": target_type,
                "target_identifier": target_identifier,
                "champion_model": champion["model_name"],
                "trained_at": datetime.utcnow().isoformat(),
                "leaderboard": [
                    {"name": item["model_name"], "metrics": item["metrics"]}
                    for item in leaderboard
                ],
                "artifact_path": str(artifact_path.resolve())
            }, f, indent=2)

        return {
            "status": "SUCCESS",
            "target": target_identifier,
            "champion": champion["model_name"],
            "leaderboard": [
                {"name": item["model_name"], "metrics": item["metrics"]}
                for item in leaderboard
            ],
            "forecast_points": len(persisted_records)
        }


def run_all_training():
    """Trains forecasting models for global revenue and top merchandise products."""
    manager = ForecastPipelineManager()

    # Clear previous forecast results to ensure fresh idempotent results
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM forecast_results;"))

    # 1. Global Daily Revenue Forecasting
    logger.info("Executing Global Daily Revenue Forecasting...")
    with engine.connect() as conn:
        df_daily = pd.read_sql(text("SELECT date_key, revenue FROM daily_sales ORDER BY date_key;"), conn)

    res_global = manager.train_and_forecast_series(
        target_type="GLOBAL_REVENUE",
        target_identifier="ALL",
        raw_series_df=df_daily,
        date_col="date_key",
        val_col="revenue"
    )

    # 2. Top 4 High-Volume Merchandise Products
    top_skus = ["22423", "85123A", "85099B", "47566"]
    product_results = []
    for sku in top_skus:
        logger.info(f"Querying historical daily demand for SKU {sku}...")
        with engine.connect() as conn:
            query = text("""
                SELECT date_key, SUM(quantity) as quantity
                FROM fact_sales
                WHERE stock_code = :sku
                GROUP BY date_key
                ORDER BY date_key;
            """)
            df_prod = pd.read_sql(query, conn, params={"sku": sku})

        res_p = manager.train_and_forecast_series(
            target_type="PRODUCT_DEMAND",
            target_identifier=sku,
            raw_series_df=df_prod,
            date_col="date_key",
            val_col="quantity"
        )
        product_results.append(res_p)

    logger.info("[+] All demand forecasting models successfully trained and serialized!")
    return {"global": res_global, "products": product_results}


if __name__ == "__main__":
    results = run_all_training()
    print("\n--- FORECAST TRAINING SUMMARY ---")
    print(json.dumps(results, indent=2))
