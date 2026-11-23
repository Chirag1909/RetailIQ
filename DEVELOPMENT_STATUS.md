# RetailIQ: Development Status Tracker

**Project:** End-to-End Retail Intelligence & Demand Forecasting Platform  
**System Architecture:** FastAPI (Python 3.11+) + PostgreSQL / SQLite Dual-Dialect Star Schema + Scikit-Learn / XGBoost / Statsmodels + React 18 / TypeScript / Tailwind CSS / Recharts  
**Current Status:** Completed & Verified  
**Last Updated:** Phase 8 Final Verification  

---

## Execution Phases & Deliverables

### Phase 1: Project Initialization, Architecture & Dataset Setup
- [x] Initialized Git repository and enterprise `.gitignore`
- [x] Verified local environment (Python 3.13.7, Node v22.19.0, npm 10.9.3, XGBoost, Statsmodels, Pandas, SQLAlchemy, FastAPI)
- [x] Established project directory structure
- [x] Dataset setup script (`scripts/download_dataset.py`) supporting the official UCI Online Retail dataset (local copy / remote archive fetch)
- [x] Converted raw 23.7 MB dataset to high-performance CSV (`data/raw/online_retail.csv`, 541,909 records)

### Phase 2: Data Ingestion, Cleaning, Validation & EDA
- [x] Ingestion module (`pipeline/extract.py`): schema validation, metadata auditing, format support
- [x] Reusable data cleaning module (`pipeline/transform.py`):
  - Missing CustomerID segregation and tracking (135,037 guest transactions)
  - Duplicate detection and removal (5,268 records removed)
  - Cancellations detection (9,251 records prefixed with 'C')
  - Negative quantity & non-merchandise code filtering (`POST`, `D`, `CR`, `BANK CHARGES`)
  - UnitPrice validation (2,512 zero/negative price rows removed)
  - Date normalization & total revenue calculation (`Quantity * UnitPrice`)
  - Yield: **522,710 verified transactions** generating **£10,266,018.19 total revenue**
- [x] Data validation reporting (`pipeline/data_quality.py`): automated quality metrics, anomaly detection, output JSON report (`data/reports/data_quality_report.json`, **94.8 / 100 Health Score**)
- [x] Comprehensive Exploratory Data Analysis (EDA) module with Plotly & Pandas (`pipeline/eda.py`):
  - Temporal aggregations (monthly, daily, weekly, intraday hourly)
  - Geographic revenue concentration (UK 85.1%, Netherlands, EIRE, Germany, France)
  - Product Pareto analysis (Top 20% SKUs yield 79.4% revenue)
  - Customer purchase frequencies, AOV (£518.70), repeat metrics (65.6%)
  - Standalone HTML EDA Report with written executive interpretations (`data/reports/eda_report.html`)

### Phase 3: Database Design, ETL Pipeline & Advanced SQL Analytics
- [x] Star-Schema Database Design (`database/schema.sql`):
  - `dim_date`: 374 calendar days with year, quarter, month, day, is_weekend
  - `dim_product`: 3,805 catalog SKUs with lifetime revenue and velocity
  - `dim_customer`: 4,334 identified accounts with geography and RFM segments
  - `fact_sales`: 522,710 transaction rows with composite uniqueness constraints
  - `daily_sales` & `monthly_sales`: Pre-aggregated time-series tables
  - `product_metrics` & `customer_metrics`: Velocity rankings and RFM metrics
  - `forecast_results`: Multi-horizon ML prediction storage
  - `inventory_parameters`: Configurable replenishment attributes
  - `pipeline_runs`: Execution audit logs
  - `data_quality_reports`: Health scorecard tracking
- [x] Database Schema DDL: `database/schema.sql` (PostgreSQL) and SQLAlchemy models (`backend/app/models/entities.py`)
- [x] Analytical SQL Views: `database/views.sql` (monthly growth, top products, country performance, repeat customers)
- [x] Advanced Analytical SQL script: `database/analytical_queries.sql` (22 production-grade queries with CTEs, Window functions, RANK, DENSE_RANK, LAG, rolling moving averages, RFM quantiles, and basket affinity)
- [x] Validated live execution of SQL queries and views against the database (`scripts/test_analytical_queries.py`)
- [x] Automated, idempotent Python ETL orchestrator (`pipeline/run_pipeline.py`) with 7 stages, retries, and audit logging

### Phase 4: Demand Forecasting Engine & Model Evaluation
- [x] Time-series feature engineering (`ml/features/builder.py`):
  - Multi-lag features (Lag 1, 7, 14, 28)
  - Rolling statistics (Rolling mean 7, 14, 28; rolling std 7, 14, 28)
  - Calendar attributes (Day of week, Month, Week of year, Weekend flag, Day of month)
  - Trend indexing
- [x] Chronological Train / Test splitting with zero data leakage (last 30 days as out-of-time evaluation test)
- [x] Implementation of 3 distinct forecasting approaches (`ml/training/models.py`):
  - Baseline: Seasonal Naive Baseline (weekly cycle)
  - Statistical: Holt-Winters Exponential Smoothing (Statsmodels ETS)
  - Machine Learning: XGBoost Regressor with lag & calendar features
- [x] Evaluation Framework (`ml/evaluation/metrics.py`): MAE, RMSE, zero-safe MAPE, and WAPE
- [x] Model Training & Competitive Selection (`ml/training/trainer.py`):
  - Global Enterprise Daily Revenue: Seasonal Naive Champion (WAPE: 27.06%, RMSE: 28,333.26)
  - SKU 22423 (Regency Cakestand): XGBoost Regressor Champion (WAPE: 52.44%, RMSE: 28.62)
  - SKU 85123A (White Hanging Heart): Holt-Winters Champion (WAPE: 66.76%, RMSE: 121.45)
  - SKU 85099B (Jumbo Bag Retrospot): Holt-Winters Champion (WAPE: 80.20%, RMSE: 205.57)
  - SKU 47566 (Party Bunting): Seasonal Naive Champion (WAPE: 79.48%, RMSE: 60.37)
- [x] Serialized model artifacts to `ml/models/` and persisted 7, 30, and 90-day predictions with 95% confidence bounds to the database

### Phase 5: Inventory Optimization & Customer RFM Analytics
- [x] Inventory Decision-Support Engine (`backend/app/inventory/optimizer.py`):
  - Expected lead-time demand calculation ($\bar{d} \times L$)
  - Configurable safety stock and target service levels ($Z \times \sigma_d \times \sqrt{L}$)
  - Reorder point (ROP) calculation
  - Economic Order Quantity (EOQ) and suggested order quantity
  - Stockout risk classification (Critical, High, Medium, Low) and inventory coverage in days
  - Transparent disclosure of user-configured/simulated operational parameters
- [x] Customer Analytics & RFM Segmentation (`backend/app/analytics/rfm.py`):
  - Recency, Frequency, and Monetary quintile scores
  - Cohort segments: Champions (41.2% spend), Loyal Customers (28.6% spend), Potential Loyalists, At Risk, Hibernating
  - Separation of historical customer spend from predictive CLV

### Phase 6: FastAPI Backend Architecture
- [x] Modular FastAPI application (`backend/app/main.py`)
- [x] Complete REST API routers:
  - `/api/health` & `/api/metadata`
  - `/api/dashboard/*` (summary, revenue-trend, top-products, country-performance)
  - `/api/sales/*` (paginated sales ledger, monthly aggregates, product summaries)
  - `/api/customers/*` (summary, segments, RFM scorecards)
  - `/api/forecast/*` (multi-horizon predictions, accuracy leaderboard, models list)
  - `/api/inventory/*` (overview, reorder recommendations, dynamic parameter tuning PUT endpoint)
  - `/api/pipeline/*` (status, manual trigger, audit history)
  - `/api/data/*` (upload CSV/XLSX, quality scorecard)
- [x] CORS middleware, Pydantic schemas, dependency-injected SQLAlchemy sessions
- [x] Comprehensive automated test suite (`backend/tests/`) with 20 passing unit/integration tests

### Phase 7: Modern Enterprise React Frontend
- [x] Vite + React 18 + TypeScript + Tailwind CSS application setup
- [x] Dark Navy enterprise SaaS aesthetic (`#070b13` background, `#0d1527` surface, cyan accents `#06b6d4`)
- [x] 9 Interactive Dashboard Pages:
  1. **Executive Overview (`/`):** Real KPIs, ComposedChart (Revenue + MoM Growth), Country breakdown, Top 10 products
  2. **Sales Analytics (`/sales`):** Daily revenue area chart, granular transaction table with pagination, country filter, search, and CSV export
  3. **Product Intelligence (`/products`):** Velocity classification (High, Medium, Low), Pareto 80/20 metrics, catalog search
  4. **Customer Insights (`/customers`):** Customer Share vs Spend Share bar chart, cohort retention strategies, customer RFM ledger
  5. **Demand Forecasting (`/forecast`):** Target selector, horizon selector (7D, 30D, 90D), actual vs predicted chart with 95% confidence bounds, competitive model leaderboard
  6. **Inventory Optimization (`/inventory`):** Stockout risk table, interactive **Tune Parameters modal** that updates the database and recalculates safety stock in real time
  7. **Data Pipeline (`/pipeline`):** Live execution monitor, 7-stage architecture diagram, execution history table, manual run button
  8. **Data Quality (`/quality`):** 94.8/100 health scorecard, transparent mathematical formula, anomaly audit, exportable report
  9. **Settings (`/settings`):** Database connection status, runtime environment details, custom CSV dataset upload form
- [x] Production build validated: `npm run build` succeeds in 12.37s with zero compilation errors

### Phase 8: Quality Assurance, Power BI Assets & Production Readiness
- [x] Power BI Preparation (`powerbi/`):
  - `powerbi/dax_measures.md`: Standard DAX measures (Total Revenue, Orders, MoM Growth %, Moving Averages, Repeat Rate %, Pareto Cumulative Share %)
  - `powerbi/dashboard_design.md`: Visual layout specifications for 5 report pages
- [x] Automated Test Suite: 20 passed tests in `backend/tests/`
- [x] GitHub Actions CI workflow (`.github/workflows/ci.yml`)
- [x] Vercel SPA routing configuration (`frontend/vercel.json`, `frontend/.env.example`)
- [x] Technical Documentation:
  - Master `README.md` covering all 23 required sections
  - `docs/architecture.md` with Mermaid diagrams
  - `docs/data_dictionary.md`
  - `docs/interview_preparation.md` with 32 in-depth technical Q&As
