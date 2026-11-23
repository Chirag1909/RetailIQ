"""
RetailIQ - Inventory Optimization Engine (backend/app/inventory/optimizer.py)
Provides decision-support calculations for replenishment, stockout risk assessment,
safety stock sizing, and EOQ based on user-configurable operational parameters.
"""

import math
from typing import Dict, Any, Optional
import numpy as np


class InventoryOptimizer:
    """Calculates scientific replenishment thresholds and risk classifications."""

    # Standard normal distribution Z-scores for service levels
    Z_SCORE_MAP = {
        90.0: 1.282,
        95.0: 1.645,
        98.0: 2.054,
        99.0: 2.326,
        99.9: 3.090
    }

    @classmethod
    def get_z_score(cls, service_level_pct: float) -> float:
        """Find closest or interpolated Z-score."""
        levels = sorted(cls.Z_SCORE_MAP.keys())
        if service_level_pct in cls.Z_SCORE_MAP:
            return cls.Z_SCORE_MAP[service_level_pct]
        # Linear approximation for arbitrary service levels between 80% and 99.9%
        clamped = max(80.0, min(99.9, service_level_pct))
        return float(np.interp(clamped, levels, [cls.Z_SCORE_MAP[k] for k in levels]))

    @classmethod
    def evaluate_inventory(
        cls,
        stock_code: str,
        current_stock: int,
        lead_time_days: int = 14,
        service_level_pct: float = 95.0,
        holding_cost: float = 1.50,
        reorder_cost: float = 25.00,
        daily_demand_mean: float = 5.0,
        daily_demand_std: float = 2.0,
        target_stock_days: int = 45
    ) -> Dict[str, Any]:
        """
        Calculates all inventory optimization metrics with actionable business narrative.
        
        Formulas:
        - Lead Time Demand = Daily Demand Mean * Lead Time Days
        - Safety Stock = Z * sqrt(Lead Time Days) * Daily Demand Std
        - Reorder Point (ROP) = Lead Time Demand + Safety Stock
        - Economic Order Quantity (EOQ) = sqrt((2 * Annual Demand * Reorder Cost) / Holding Cost)
        - Target Stock = Daily Demand Mean * Target Stock Days
        - Suggested Reorder Quantity = max(0, Target Stock - Current Stock)
        - Inventory Coverage (Days) = Current Stock / Daily Demand Mean
        """
        d_mean = max(0.01, float(daily_demand_mean))
        d_std = max(0.01, float(daily_demand_std))
        lt = max(1, int(lead_time_days))
        z = cls.get_z_score(service_level_pct)

        # Core formulas
        lead_time_demand = round(d_mean * lt, 2)
        safety_stock = int(math.ceil(z * math.sqrt(lt) * d_std))
        reorder_point = int(math.ceil(lead_time_demand + safety_stock))

        # EOQ
        annual_demand = d_mean * 365.0
        h_cost = max(0.1, float(holding_cost))
        r_cost = max(1.0, float(reorder_cost))
        eoq = int(math.ceil(math.sqrt((2 * annual_demand * r_cost) / h_cost)))

        # Target Stock and suggested reorder
        target_stock = int(math.ceil(d_mean * target_stock_days))
        suggested_reorder_qty = max(0, target_stock - current_stock)

        # Coverage in days
        coverage_days = round(current_stock / d_mean, 1)

        # Risk Classification
        if current_stock <= 0:
            stockout_risk = "Critical"
            status_summary = "STOCKOUT: Item is completely depleted. Expedite immediate purchase order."
        elif current_stock < safety_stock:
            stockout_risk = "Critical"
            status_summary = f"CRITICAL BUFFER BREACH: Stock is below safety threshold ({safety_stock} units). High risk of supplier stockout."
        elif current_stock <= reorder_point:
            stockout_risk = "High"
            status_summary = f"REORDER TRIGGERED: Current inventory ({current_stock}) is below Reorder Point ({reorder_point}). Place replenishment order."
        elif coverage_days < lt:
            stockout_risk = "Medium"
            status_summary = "APPROACHING REORDER: Current stock is sufficient for lead time but replenishment window approaching."
        else:
            stockout_risk = "Low"
            status_summary = f"HEALTHY BUFFER: Adequate supply for {coverage_days} days of forecast demand."

        # Overstock Risk
        if coverage_days > 90:
            overstock_risk = "High"
            overstock_summary = f"CAPITAL LOCK-UP: {coverage_days} days of inventory exceeds normal 90-day threshold. Consider promotional clearance."
        elif coverage_days > 60:
            overstock_risk = "Medium"
            overstock_summary = "Elevated inventory holding. Monitor demand velocity."
        else:
            overstock_risk = "Low"
            overstock_summary = "Lean inventory balance."

        return {
            "stock_code": stock_code,
            "configured_parameters": {
                "current_stock": current_stock,
                "lead_time_days": lt,
                "service_level_pct": service_level_pct,
                "holding_cost": h_cost,
                "reorder_cost": r_cost,
                "target_stock_days": target_stock_days,
                "is_simulated": True
            },
            "demand_assumptions": {
                "daily_demand_mean": round(d_mean, 2),
                "daily_demand_std": round(d_std, 2),
                "annual_forecast_demand": round(annual_demand, 1)
            },
            "recommendations": {
                "lead_time_demand": lead_time_demand,
                "safety_stock": safety_stock,
                "reorder_point": reorder_point,
                "suggested_reorder_quantity": suggested_reorder_qty,
                "economic_order_quantity_eoq": eoq,
                "inventory_coverage_days": coverage_days,
                "stockout_risk_level": stockout_risk,
                "overstock_risk_level": overstock_risk,
                "action_recommendation": status_summary,
                "overstock_recommendation": overstock_summary
            }
        }
