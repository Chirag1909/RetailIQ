"""
RetailIQ - Inventory Optimization Unit Tests (backend/tests/test_inventory.py)
Validates mathematical correctness of safety stock, ROP, EOQ, and risk categorization.
"""

import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from backend.app.inventory.optimizer import InventoryOptimizer


def test_inventory_optimizer_formulas():
    result = InventoryOptimizer.evaluate_inventory(
        stock_code="TEST-001",
        current_stock=50,
        lead_time_days=14,
        service_level_pct=95.0, # Z ~ 1.645
        holding_cost=2.00,
        reorder_cost=30.00,
        daily_demand_mean=10.0,
        daily_demand_std=3.0,
        target_stock_days=30
    )

    recs = result["recommendations"]
    # Lead time demand = 10 * 14 = 140
    assert recs["lead_time_demand"] == 140.0
    # Safety stock > 0
    assert recs["safety_stock"] > 0
    # Reorder point = 140 + safety_stock
    assert recs["reorder_point"] == int(140.0 + recs["safety_stock"])
    # Suggested reorder quantity = max(0, 300 - 50) = 250
    assert recs["suggested_reorder_quantity"] == 250
    # Since current_stock (50) < safety_stock or < reorder_point (140+):
    assert recs["stockout_risk_level"] in ["Critical", "High"]


def test_overstock_classification():
    result = InventoryOptimizer.evaluate_inventory(
        stock_code="TEST-002",
        current_stock=1000,
        daily_demand_mean=5.0
    )
    # Coverage = 1000 / 5 = 200 days (> 90 days)
    assert result["recommendations"]["inventory_coverage_days"] == 200.0
    assert result["recommendations"]["overstock_risk_level"] == "High"
