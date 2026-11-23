"""
RetailIQ - Application Configuration (backend/app/core/config.py)
Manages environment variables, CORS origins, API routing, and DB connection strings.
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "RetailIQ"
    PROJECT_DESCRIPTION: str = "End-to-End Retail Intelligence & Demand Forecasting Platform"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'retailiq.db').as_posix()}"
    )

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
