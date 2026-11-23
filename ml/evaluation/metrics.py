"""
RetailIQ - Time-Series Forecast Evaluation Metrics (ml/evaluation/metrics.py)
Provides standard evaluation metrics: MAE, RMSE, MAPE (zero-safe), and WAPE.
"""

from typing import Dict
import numpy as np


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes genuine time-series forecasting evaluation metrics.
    Zero-safe for days with 0 retail revenue/demand.
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    # Clip negative forecasts to zero for non-negative demand/sales
    y_p = np.clip(y_p, 0.0, None)

    mae = float(np.mean(np.abs(y_t - y_p)))
    rmse = float(np.sqrt(np.mean((y_t - y_p) ** 2)))

    # Zero-safe MAPE
    denom = np.where(y_t == 0, 1.0, y_t)
    mape = float(np.mean(np.abs((y_t - y_p) / denom)) * 100.0)

    # WAPE: sum(|y - y_hat|) / sum(y)
    sum_true = float(np.sum(y_t))
    wape = float((np.sum(np.abs(y_t - y_p)) / max(sum_true, 1e-6)) * 100.0)

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 4),
        "wape": round(wape, 4)
    }
