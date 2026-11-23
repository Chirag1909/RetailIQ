"""
RetailIQ - Time-Series Forecasting & ML Validation Tests (backend/tests/test_forecasting.py)
Validates chronological non-shuffled splitting, leak prevention, and metric calculations.
"""

import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
import numpy as np
import pandas as pd
from ml.features.builder import prepare_time_series_frame, build_forecasting_features, chronological_train_test_split
from ml.evaluation.metrics import compute_metrics
from ml.training.models import SeasonalNaiveModel, XGBoostForecaster


def test_chronological_splitting():
    dates = pd.date_range("2021-01-01", periods=100, freq="D")
    df = pd.DataFrame({"date_key": dates, "revenue": np.arange(100)})
    ts_df = prepare_time_series_frame(df)
    feat_df = build_forecasting_features(ts_df)

    train_df, test_df = chronological_train_test_split(feat_df, test_horizon_days=20)
    assert len(test_df) == 20
    assert train_df["date"].max() < test_df["date"].min()
    # Ensure zero overlap
    assert set(train_df["date"]).isdisjoint(set(test_df["date"]))


def test_forecast_metrics_calculation():
    y_true = np.array([100.0, 200.0, 300.0, 0.0])
    y_pred = np.array([110.0, 190.0, 300.0, 10.0])
    metrics = compute_metrics(y_true, y_pred)

    assert metrics["mae"] == 7.5
    assert metrics["rmse"] > 0
    assert metrics["wape"] > 0
    assert "mape" in metrics


def test_seasonal_naive_forecast():
    history = np.array([10, 20, 30, 40, 50, 60, 70] * 3)
    model = SeasonalNaiveModel(season_length=7)
    model.fit(history)
    preds = model.predict(steps=14)
    assert len(preds) == 14
    assert np.array_equal(preds[:7], history[-7:])
