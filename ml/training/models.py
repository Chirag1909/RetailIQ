"""
RetailIQ - Time-Series Forecasting Models (ml/training/models.py)
Implements:
1. Seasonal Naive / Naive Baseline
2. Holt-Winters Exponential Smoothing (Statsmodels)
3. XGBoost Lag-Based ML Forecaster
"""

import sys
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except ImportError:
    ExponentialSmoothing = None

try:
    import xgboost as xgb
except ImportError:
    xgb = None

from sklearn.ensemble import RandomForestRegressor
from ml.evaluation.metrics import compute_metrics


class SeasonalNaiveModel:
    """Model 1: Seasonal Naive baseline projecting weekly (7-day) periodicity."""

    def __init__(self, season_length: int = 7):
        self.season_length = season_length
        self.history = None

    def fit(self, y_train: np.ndarray):
        self.history = np.array(y_train)
        return self

    def predict(self, steps: int) -> np.ndarray:
        if len(self.history) < self.season_length:
            return np.repeat(self.history[-1], steps)
        # Repeat last seasonal cycle
        last_season = self.history[-self.season_length:]
        repeats = int(np.ceil(steps / self.season_length))
        preds = np.tile(last_season, repeats)[:steps]
        return np.clip(preds, 0, None)


class StatisticalExpSmoothingModel:
    """Model 2: Holt-Winters Exponential Smoothing with trend & seasonal modeling."""

    def __init__(self, seasonal_periods: int = 7):
        self.seasonal_periods = seasonal_periods
        self.model_fitted = None
        self.last_val = 0.0

    def fit(self, y_train: np.ndarray):
        y = np.array(y_train, dtype=float)
        self.last_val = y[-1] if len(y) > 0 else 0.0
        # If statsmodels is available and series has sufficient observations
        if ExponentialSmoothing and len(y) >= self.seasonal_periods * 3:
            try:
                # Add tiny offset to avoid zeros in box-cox or multiplicative
                y_adj = y + 0.01
                model = ExponentialSmoothing(
                    y_adj,
                    trend="add",
                    seasonal="add",
                    seasonal_periods=self.seasonal_periods,
                    initialization_method="estimated"
                )
                self.model_fitted = model.fit(optimized=True)
            except Exception:
                try:
                    model = ExponentialSmoothing(y, trend="add", seasonal=None)
                    self.model_fitted = model.fit()
                except Exception:
                    self.model_fitted = None
        return self

    def predict(self, steps: int) -> np.ndarray:
        if self.model_fitted:
            preds = self.model_fitted.forecast(steps)
            return np.clip(np.array(preds), 0, None)
        # Fallback to moving average if HW fitting encountered divergence
        return np.repeat(self.last_val, steps)


class XGBoostForecaster:
    """Model 3: Gradient Boosted Trees utilizing lag, rolling, and calendar signals."""

    def __init__(self):
        self.feature_cols = [
            "day_of_week", "day_of_month", "month", "week_of_year", "is_weekend",
            "trend_index", "lag_1", "lag_7", "lag_14", "lag_28",
            "rolling_mean_7", "rolling_std_7", "rolling_mean_14", "rolling_std_14",
            "rolling_mean_28", "rolling_std_28"
        ]
        self.model = None

    def fit(self, train_df: pd.DataFrame):
        X_train = train_df[self.feature_cols]
        y_train = train_df["y"]

        if xgb is not None:
            self.model = xgb.XGBRegressor(
                n_estimators=120,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.85,
                colsample_bytree=0.85,
                random_state=42,
                n_jobs=-1
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=6,
                random_state=42,
                n_jobs=-1
            )
        self.model.fit(X_train, y_train)
        return self

    def predict_features(self, test_df: pd.DataFrame) -> np.ndarray:
        X_test = test_df[self.feature_cols]
        preds = self.model.predict(X_test)
        return np.clip(preds, 0, None)

    def recursive_forecast(self, history_df: pd.DataFrame, horizon_days: int) -> Tuple[pd.DatetimeIndex, np.ndarray]:
        """
        Generates genuine multi-step ahead forecasts recursively updating lags and rolling stats.
        """
        curr_df = history_df.copy()
        last_date = curr_df["date"].max()
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon_days, freq="D")

        preds = []
        for next_date in future_dates:
            # Build current feature row
            day_of_week = next_date.dayofweek
            day_of_month = next_date.day
            month = next_date.month
            week_of_year = int(next_date.isocalendar().week)
            is_weekend = 1 if day_of_week in [5, 6] else 0
            trend_index = len(curr_df)

            recent_y = curr_df["y"].values
            lag_1 = recent_y[-1]
            lag_7 = recent_y[-7] if len(recent_y) >= 7 else lag_1
            lag_14 = recent_y[-14] if len(recent_y) >= 14 else lag_1
            lag_28 = recent_y[-28] if len(recent_y) >= 28 else lag_1

            r_mean_7 = float(np.mean(recent_y[-7:]))
            r_std_7 = float(np.std(recent_y[-7:]))
            r_mean_14 = float(np.mean(recent_y[-14:]))
            r_std_14 = float(np.std(recent_y[-14:]))
            r_mean_28 = float(np.mean(recent_y[-28:]))
            r_std_28 = float(np.std(recent_y[-28:]))

            row_feat = pd.DataFrame([{
                "day_of_week": day_of_week,
                "day_of_month": day_of_month,
                "month": month,
                "week_of_year": week_of_year,
                "is_weekend": is_weekend,
                "trend_index": trend_index,
                "lag_1": lag_1,
                "lag_7": lag_7,
                "lag_14": lag_14,
                "lag_28": lag_28,
                "rolling_mean_7": r_mean_7,
                "rolling_std_7": r_std_7,
                "rolling_mean_14": r_mean_14,
                "rolling_std_14": r_std_14,
                "rolling_mean_28": r_mean_28,
                "rolling_std_28": r_std_28,
            }])

            pred_val = float(np.clip(self.model.predict(row_feat[self.feature_cols])[0], 0, None))
            preds.append(pred_val)

            # Append prediction to history to feed subsequent lags
            curr_df = pd.concat([curr_df, pd.DataFrame([{"date": next_date, "y": pred_val}])], ignore_index=True)

        return future_dates, np.array(preds)
