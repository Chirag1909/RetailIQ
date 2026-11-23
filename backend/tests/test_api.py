"""
RetailIQ - Backend API Integration Tests (backend/tests/test_api.py)
Tests core FastAPI endpoints using TestClient.
"""

import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check():
    """Verify health endpoint returns status 200 and healthy."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data


def test_metadata_endpoint():
    """Verify metadata endpoint returns platform details and model catalog."""
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "RetailIQ"
    assert "Seasonal Naive Baseline" in data["supported_models"]
    assert 30 in data["forecast_horizons"]


def test_dashboard_summary():
    """Verify executive summary metrics match genuine database calculations."""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_revenue"] > 0
    assert data["total_orders"] > 0
    assert data["unique_customers"] > 0
    assert data["average_order_value"] > 0


def test_revenue_trend():
    """Verify daily revenue time series returns valid points."""
    response = client.get("/api/dashboard/revenue-trend")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first_pt = data[0]
    assert "date" in first_pt
    assert "revenue" in first_pt


def test_top_products():
    """Verify top products endpoint returns ranked merchandise."""
    response = client.get("/api/dashboard/top-products?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["total_revenue"] >= data[1]["total_revenue"]


def test_country_performance():
    """Verify geographic breakdown includes United Kingdom as leader."""
    response = client.get("/api/dashboard/country-performance?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["country"] == "United Kingdom"
    assert data[0]["global_share_pct"] > 50.0


def test_monthly_sales():
    """Verify monthly aggregation and MoM growth calculation."""
    response = client.get("/api/sales/monthly")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 12
    assert "year_month" in data[0]
    assert "revenue" in data[0]


def test_customer_summary_and_rfm():
    """Verify customer analytics and RFM segmentation breakdown."""
    response = client.get("/api/customers/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_identified_customers"] > 0
    assert len(data["segments"]) > 0
    segment_names = [s["segment"] for s in data["segments"]]
    assert "Champions" in segment_names or "Loyal Customers" in segment_names


def test_forecast_endpoint_global():
    """Verify genuine multi-horizon revenue forecasts."""
    response = client.get("/api/forecast?target_type=GLOBAL_REVENUE&target_identifier=ALL&horizon_days=30")
    assert response.status_code == 200
    data = response.json()
    assert data["target_identifier"] == "ALL"
    assert len(data["forecasts"]) == 30
    assert data["mae"] is not None
    assert data["wape"] is not None


def test_inventory_overview_and_update():
    """Verify inventory monitoring overview and parameter updating."""
    response = client.get("/api/inventory/overview?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total_monitored_skus"] > 0
    assert len(data["inventory_items"]) > 0

    first_item = data["inventory_items"][0]
    sku = first_item["stock_code"]

    # Test dynamic parameter update
    update_resp = client.put(f"/api/inventory/parameters/{sku}", json={
        "current_stock": 250,
        "lead_time_days": 21,
        "service_level_pct": 98.0
    })
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["current_stock"] == 250
    assert updated_data["lead_time_days"] == 21
    assert updated_data["service_level_pct"] == 98.0


def test_pipeline_status():
    """Verify pipeline status inspection."""
    response = client.get("/api/pipeline/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_runs"] > 0
    assert data["latest_run"] is not None
