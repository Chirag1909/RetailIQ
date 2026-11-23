"""
RetailIQ - FastAPI Main Application Gateway (backend/app/main.py)
Integrates Enterprise Analytics, Machine Learning Demand Forecasting,
Inventory Optimization, and Data Pipeline Orchestration.
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.core.config import settings
from backend.app.database.session import init_db
from backend.app.api.health import router as health_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.sales import router as sales_router
from backend.app.api.customers import router as customers_router
from backend.app.api.forecast import router as forecast_router
from backend.app.api.inventory import router as inventory_router
from backend.app.api.pipeline import router as pipeline_router
from backend.app.api.data import router as data_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RetailIQ-Backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    logger.info("Initializing RetailIQ database schema and analytical views...")
    init_db()
    logger.info("RetailIQ platform backend successfully started.")
    yield
    logger.info("RetailIQ platform backend shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular API Routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(sales_router, prefix=settings.API_V1_STR)
app.include_router(customers_router, prefix=settings.API_V1_STR)
app.include_router(forecast_router, prefix=settings.API_V1_STR)
app.include_router(inventory_router, prefix=settings.API_V1_STR)
app.include_router(pipeline_router, prefix=settings.API_V1_STR)
app.include_router(data_router, prefix=settings.API_V1_STR)

# Serve generated HTML reports statically
reports_dir = BASE_DIR / "data" / "reports"
if reports_dir.exists():
    app.mount("/reports", StaticFiles(directory=str(reports_dir)), name="reports")


@app.get("/")
def root_redirect():
    """Root redirect and welcome endpoint."""
    return {
        "project": "RetailIQ - End-to-End Retail Intelligence & Demand Forecasting Platform",
        "documentation": "/docs",
        "health_check": "/api/health",
        "eda_report": "/reports/eda_report.html"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
