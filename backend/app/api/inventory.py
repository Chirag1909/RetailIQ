"""
RetailIQ - Inventory Optimization Endpoints (backend/app/api/inventory.py)
Provides replenishment calculations, risk auditing, and dynamic parameter tuning.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import (
    InventoryOverviewResponse, InventoryItem, InventoryParamUpdateRequest
)
from backend.app.inventory.optimizer import InventoryOptimizer

router = APIRouter(prefix="/inventory", tags=["Inventory Optimization"])


@router.get("/overview", response_model=InventoryOverviewResponse)
def get_inventory_overview(
    risk_level: Optional[str] = Query(None, description="Critical, High, Medium, Low"),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Returns inventory health KPIs and monitored product replenishment status."""
    # Summary stats
    stats = db.execute(text("""
        SELECT 
            COUNT(*) as total_skus,
            COALESCE(SUM(CASE WHEN stockout_risk_level = 'Critical' THEN 1 ELSE 0 END), 0) as crit,
            COALESCE(SUM(CASE WHEN stockout_risk_level = 'High' THEN 1 ELSE 0 END), 0) as high,
            COALESCE(SUM(CASE WHEN overstock_risk_level = 'High' THEN 1 ELSE 0 END), 0) as over,
            COALESCE(AVG(inventory_coverage_days), 0.0) as avg_cov
        FROM inventory_parameters;
    """)).fetchone()

    total_skus = int(stats[0]) if stats else 0
    crit = int(stats[1]) if stats else 0
    high = int(stats[2]) if stats else 0
    over = int(stats[3]) if stats else 0
    avg_cov = round(float(stats[4]), 1) if stats else 0.0

    # Query items
    query = """
        SELECT 
            i.stock_code, p.description, i.current_stock, i.lead_time_days,
            i.service_level_pct, i.expected_lead_time_demand, i.safety_stock,
            i.reorder_point, i.suggested_reorder_qty, i.inventory_coverage_days,
            i.stockout_risk_level, i.overstock_risk_level
        FROM inventory_parameters i
        JOIN dim_product p ON i.stock_code = p.stock_code
        WHERE 1=1
    """
    params = {"limit": limit}
    if risk_level and risk_level != "ALL":
        query += " AND i.stockout_risk_level = :risk"
        params["risk"] = risk_level
    if search:
        query += " AND (i.stock_code LIKE :search OR p.description LIKE :search)"
        params["search"] = f"%{search}%"

    query += " ORDER BY CASE i.stockout_risk_level WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, i.inventory_coverage_days ASC LIMIT :limit;"

    rows = db.execute(text(query), params).fetchall()
    items = []
    for r in rows:
        items.append(InventoryItem(
            stock_code=r[0],
            description=r[1],
            current_stock=int(r[2]),
            lead_time_days=int(r[3]),
            service_level_pct=float(r[4]),
            expected_lead_time_demand=float(r[5]),
            safety_stock=int(r[6]),
            reorder_point=int(r[7]),
            suggested_reorder_qty=int(r[8]),
            inventory_coverage_days=float(r[9]),
            stockout_risk_level=r[10],
            overstock_risk_level=r[11],
            action_recommendation=f"Risk: {r[10]}. Reorder point: {r[7]} units."
        ))

    return InventoryOverviewResponse(
        total_monitored_skus=total_skus,
        critical_stockout_count=crit,
        high_stockout_count=high,
        overstock_risk_count=over,
        average_coverage_days=avg_cov,
        inventory_items=items
    )


@router.get("/recommendations", response_model=List[InventoryItem])
def get_inventory_recommendations(
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Returns prioritized products requiring immediate replenishment order placement."""
    rows = db.execute(text("""
        SELECT 
            i.stock_code, p.description, i.current_stock, i.lead_time_days,
            i.service_level_pct, i.expected_lead_time_demand, i.safety_stock,
            i.reorder_point, i.suggested_reorder_qty, i.inventory_coverage_days,
            i.stockout_risk_level, i.overstock_risk_level
        FROM inventory_parameters i
        JOIN dim_product p ON i.stock_code = p.stock_code
        WHERE i.stockout_risk_level IN ('Critical', 'High')
        ORDER BY i.current_stock ASC
        LIMIT :limit;
    """), {"limit": limit}).fetchall()

    return [
        InventoryItem(
            stock_code=r[0],
            description=r[1],
            current_stock=int(r[2]),
            lead_time_days=int(r[3]),
            service_level_pct=float(r[4]),
            expected_lead_time_demand=float(r[5]),
            safety_stock=int(r[6]),
            reorder_point=int(r[7]),
            suggested_reorder_qty=int(r[8]),
            inventory_coverage_days=float(r[9]),
            stockout_risk_level=r[10],
            overstock_risk_level=r[11],
            action_recommendation=f"Replenish immediately: {r[8]} units suggested."
        )
        for r in rows
    ]


@router.put("/parameters/{product_id}", response_model=InventoryItem)
def update_inventory_parameters(
    product_id: str = Path(..., description="StockCode of product"),
    params: InventoryParamUpdateRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Dynamically recalculates replenishment thresholds with updated user assumptions.
    """
    # Fetch product metadata and current parameters
    row = db.execute(text("""
        SELECT i.stock_code, p.description, i.current_stock, i.lead_time_days,
               i.service_level_pct, i.holding_cost, i.reorder_cost, p.total_lifetime_quantity
        FROM inventory_parameters i
        JOIN dim_product p ON i.stock_code = p.stock_code
        WHERE i.stock_code = :sku;
    """), {"sku": product_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Product SKU {product_id} not found in inventory catalog.")

    curr_stock = params.current_stock if params.current_stock is not None else int(row[2])
    lt = params.lead_time_days if params.lead_time_days is not None else int(row[3])
    sl = params.service_level_pct if params.service_level_pct is not None else float(row[4])
    h_cost = params.holding_cost if params.holding_cost is not None else float(row[5])
    r_cost = params.reorder_cost if params.reorder_cost is not None else float(row[6])

    tot_qty = float(row[7])
    daily_mean = max(0.5, tot_qty / 365.0)
    daily_std = max(0.2, daily_mean * 0.45)

    eval_res = InventoryOptimizer.evaluate_inventory(
        stock_code=product_id,
        current_stock=curr_stock,
        lead_time_days=lt,
        service_level_pct=sl,
        holding_cost=h_cost,
        reorder_cost=r_cost,
        daily_demand_mean=daily_mean,
        daily_demand_std=daily_std
    )

    recs = eval_res["recommendations"]

    # Update database
    db.execute(text("""
        UPDATE inventory_parameters
        SET current_stock = :cs,
            lead_time_days = :lt,
            service_level_pct = :sl,
            holding_cost = :hc,
            reorder_cost = :rc,
            expected_lead_time_demand = :ltd,
            safety_stock = :ss,
            reorder_point = :rop,
            suggested_reorder_qty = :srq,
            inventory_coverage_days = :cov,
            stockout_risk_level = :srl,
            overstock_risk_level = :orl,
            last_evaluated_at = :now
        WHERE stock_code = :sku;
    """), {
        "cs": curr_stock,
        "lt": lt,
        "sl": sl,
        "hc": h_cost,
        "rc": r_cost,
        "ltd": recs["lead_time_demand"],
        "ss": recs["safety_stock"],
        "rop": recs["reorder_point"],
        "srq": recs["suggested_reorder_quantity"],
        "cov": recs["inventory_coverage_days"],
        "srl": recs["stockout_risk_level"],
        "orl": recs["overstock_risk_level"],
        "now": datetime.utcnow(),
        "sku": product_id
    })
    db.commit()

    return InventoryItem(
        stock_code=product_id,
        description=row[1],
        current_stock=curr_stock,
        lead_time_days=lt,
        service_level_pct=sl,
        expected_lead_time_demand=recs["lead_time_demand"],
        safety_stock=recs["safety_stock"],
        reorder_point=recs["reorder_point"],
        suggested_reorder_qty=recs["suggested_reorder_quantity"],
        inventory_coverage_days=recs["inventory_coverage_days"],
        stockout_risk_level=recs["stockout_risk_level"],
        overstock_risk_level=recs["overstock_risk_level"],
        action_recommendation=recs["action_recommendation"]
    )
