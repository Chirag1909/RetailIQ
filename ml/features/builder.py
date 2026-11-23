"""
RetailIQ - Time-Series Feature Engineering Engine (ml/features/builder.py)
Constructs leak-free chronological lag, rolling statistical, and calendar features.
Enforces strict chronological train-test splitting.
"""

import sys
from pathlib import Path
from typing import Tuple, List, Optional
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def prepare_time_series_frame(
    df_daily: pd.DataFrame,
    date_col: str = "date_key",
    value_col: str = "revenue"
) -> pd.DataFrame:
    """
    Ensures complete chronological date index without gaps (fills non-trading days with 0).
    """
    ts_df = df_daily[[date_col, value_col]].copy()
    ts_df[date_col] = pd.to_datetime(ts_df[date_col])
    ts_df = ts_df.sort_values(date_col).drop_duplicates(subset=[date_col])
    ts_df.set_index(date_col, inplace=True)

    # Reindex to full daily frequency
    full_idx = pd.date_range(start=ts_df.index.min(), end=ts_df.index.max(), freq="D")
    ts_df = ts_df.reindex(full_idx, fill_value=0.0)
    ts_df.index.name = "date"
    ts_df.reset_index(inplace=True)
    ts_df.rename(columns={value_col: "y"}, inplace=True)
    return ts_df


def build_forecasting_features(
    ts_df: pd.DataFrame,
    lags: List[int] = [1, 7, 14, 28],
    rolling_windows: List[int] = [7, 14, 28]
) -> pd.DataFrame:
    """
    Constructs time-series features without data leakage.
    Rolling statistics are computed on shifted values (lag 1).
    """
    df = ts_df.copy()
    df = df.sort_values("date").reset_index(drop=True)

    # 1. Calendar Features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["trend_index"] = np.arange(len(df))

    # 2. Lag Features
    for lag in lags:
        df[f"lag_{lag}"] = df["y"].shift(lag)

    # 3. Rolling Statistics (computed on lag 1 to prevent target leakage)
    shifted_target = df["y"].shift(1)
    for window in rolling_windows:
        df[f"rolling_mean_{window}"] = shifted_target.rolling(window=window).mean()
        df[f"rolling_std_{window}"] = shifted_target.rolling(window=window).std().fillna(0.0)

    # Drop early rows containing NaN from lags
    max_lag = max(max(lags), max(rolling_windows))
    df = df.iloc[max_lag:].reset_index(drop=True)
    return df


def chronological_train_test_split(
    df: pd.DataFrame,
    test_horizon_days: int = 30
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs deterministic, non-shuffled chronological train/test split.
    Guarantees test set strictly follows train set.
    """
    if len(df) <= test_horizon_days + 14:
        raise ValueError(f"Insufficient time-series history ({len(df)} points) for {test_horizon_days}-day test horizon.")

    split_idx = len(df) - test_horizon_days
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    return train_df, test_df
