# RetailIQ: End-to-End Retail Intelligence & Demand Forecasting Platform

[![CI Pipeline](https://github.com/your-username/retailiq/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/retailiq/actions)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Project Introduction

**RetailIQ** is a production-grade, end-to-end retail intelligence and machine learning demand forecasting platform. It transforms raw, messy e-commerce transaction logs into high-leverage business decisions, automated replenishments, customer behavioral segmentations, and multi-horizon demand forecasts.

Designed with an enterprise SaaS dark-mode visual language, RetailIQ integrates a Python ETL engine, a Star-Schema analytical data warehouse (PostgreSQL / SQLite dual dialect), competitive machine learning models (Seasonal Naive, Holt-Winters Exponential Smoothing, and XGBoost Regressor), a high-performance FastAPI backend gateway, and a responsive React 18 / TypeScript single-page application.

---

## 2. Business Problem

Modern retail enterprises generate millions of transactional records annually. However, organizations frequently struggle with fragmented data silos, resulting in:
1. **Stockout Losses:** High-velocity products frequently run out of stock due to unscientific replenishment thresholds.
2. **Capital Lock-Up:** Excess inventory languishes in warehouses for months, accumulating holding costs.
3. **Churn Blindness:** High-value historical accounts quietly slip into dormancy without retention interventions.
4. **Demand Uncertainty:** Procurement teams guess future purchasing volumes instead of leveraging statistical time-series projections.
5. **Decoupled Analytics:** Dashboards show what happened in the past but fail to recommend what action decision-makers should take next.

---

## 3. Solution Overview

RetailIQ resolves these challenges by providing a unified, closed-loop analytical engine:
- **Data Engineering:** Ingests 541,909 raw records from the official UCI Online Retail repository, filtering duplicates, segregating cancellations, standardizing timestamps, and calculating revenue.
- **Relational Star Schema:** Structures transactions into fact and dimensional tables with pre-computed daily, monthly, product, and customer summary tables.
- **Machine Learning Demand Forecasting:** Forecasts daily enterprise revenue and product-level demand over 7-day, 30-day, and 90-day horizons with 95% statistical confidence bounds using strictly leak-free chronological splits.
- **Inventory Optimization:** Computes scientific Safety Stock, Reorder Points (ROP), Economic Order Quantities (EOQ), and stockout risk tiers based on configurable service-level targets.
- **Customer RFM Segmentation:** Evaluates customer Recency, Frequency, and Monetary quintile scores to segment buyers into *Champions*, *Loyal Customers*, *Potential Loyalists*, *At Risk*, and *Hibernating*.
- **Executive UI:** An enterprise dashboard providing interactive Recharts visualizations, granular transaction search, parameter tuning modals, and pipeline telemetry.

---

## 4. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Ingestion_ETL ["1. Data Engineering & ETL Pipeline"]
        RawData["UCI Online Retail Dataset\n(541,909 raw records)"] --> Extractor["pipeline/extract.py\nSchema Validation"]
        Extractor --> Cleaner["pipeline/transform.py\nDeduplication & Cancellation Flagging"]
        Cleaner --> QualityScore["pipeline/data_quality.py\nHealth Scorecard (94.8/100)"]
        Cleaner --> Aggregates["Dimensional Aggregations\n(Daily, Monthly, Product, Customer)"]
    end

    subgraph Data_Warehouse ["2. Analytical Star Schema (retailiq_db)"]
        Aggregates --> DimDate["dim_date (374 calendar days)"]
        Aggregates --> DimProduct["dim_product (3,805 SKUs)"]
        Aggregates --> DimCustomer["dim_customer (4,334 accounts)"]
        Cleaner --> FactSales["fact_sales (522,710 verified sales)"]
        FactSales --> SQLViews["7 Analytical SQL Views\n(MoM Growth, Pareto, Top SKUs)"]
    end

    subgraph ML_Analytics ["3. Machine Learning & Decision Engines"]
        FactSales --> FeatureEng["ml/features/builder.py\nLags (1,7,14,28) & Rolling Means (7,14,28)"]
        FeatureEng --> ChronoSplit["Chronological Out-of-Time Split\n(Zero Leakage)"]
        ChronoSplit --> ModelBench["Competitive Benchmark:\n- Seasonal Naive Baseline\n- Holt-Winters Exp Smoothing\n- XGBoost Regressor"]
        ModelBench --> Champion["Champion Model Selection\nMulti-Horizon (7D, 30D, 90D) Forecasts"]
        FactSales --> InvEngine["backend/app/inventory/optimizer.py\nSafety Stock, Lead Time Demand, ROP"]
        FactSales --> RFMEngine["backend/app/analytics/rfm.py\nQuintile RFM Scoring"]
    end

    subgraph API_Gateway ["4. FastAPI Gateway (:8000)"]
        Data_Warehouse & Champion & InvEngine & RFMEngine --> Routers["FastAPI Modular Routers\n/dashboard, /sales, /customers, /forecast, /inventory, /pipeline, /data"]
    end

    subgraph Presentation ["5. React 18 / TypeScript UI (:5173)"]
        Routers --> ReactApp["React 18 + Tailwind CSS + Recharts UI\nDark Navy Enterprise SaaS Experience"]
    end
```

---

## 5. Dataset Provenance & Limitations

### Official Dataset Source
- **Repository:** UCI Machine Learning Repository
- **Dataset:** Online Retail (Dataset ID: 352)
- **URL:** [https://archive.ics.uci.edu/dataset/352/online+retail](https://archive.ics.uci.edu/dataset/352/online+retail)
- **Time Span:** December 1, 2010 – December 9, 2011 (374 days)
- **Raw Dimensions:** 541,909 rows × 8 attributes

### Dataset Limitations & Operational Disclosure
The UCI dataset reflects genuine historical retail transactions but does **not** include:
1. Physical warehouse identifiers or store locations.
2. Current on-hand warehouse inventory quantities.
3. Actual supplier procurement lead times.
4. Product procurement costs or supplier wholesale contracts.
5. Customer demographics (gender, age, address).

**Engineering Resolution:**
- Country-level and product-level analytics are used instead of non-existent store IDs.
- For inventory optimization, operational parameters (current stock, lead times, service levels) are explicitly documented as **user-configured or simulated assumptions**. The platform allows users to interactively tune these parameters in real time.

---

## 6. Technology Stack

| Layer | Technologies | Rationale |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React, React Router, Axios | Type-safe, ultra-fast HMR, dark enterprise design system, composable SVG charts. |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, Pydantic V2, Uvicorn | Asynchronous performance, automatic OpenAPI documentation, dependency injection. |
| **Database** | PostgreSQL (Production) / SQLite (Local Dev Fallback), SQLAlchemy ORM | Star-schema dimensional relational modeling with dual dialect compatibility. |
| **Data Engineering**| Pandas, NumPy, PyArrow, OpenPyXL, Scipy | Vectorized transformation pipelines, high-throughput CSV parsing, audit logging. |
| **Machine Learning**| Scikit-Learn, XGBoost, Statsmodels | Chronological splitting, multi-lag feature engineering, competitive model evaluation. |
| **Testing** | Pytest, HTTPX, TestClient | Automated unit and integration test coverage across APIs, ETL, and ML logic. |
| **DevOps / CI/CD** | Git, GitHub Actions, Vercel SPA Configuration | Continuous integration pipeline validating backend tests and frontend production builds. |

---

## 7. Data Cleaning & Validation Methodology

The automated cleaning pipeline (`pipeline/transform.py`) applies deterministic business rules:
1. **Deduplication:** Identified and dropped **5,268 exact duplicate rows** to prevent volume double-counting.
2. **Cancellation Flagging:** Detected **9,251 cancellation records** (invoices prefixed with `'C'`) and segregated them from positive demand facts.
3. **Price Validation:** Filtered **2,512 zero or negative unit price entries** representing system testing or scrap.
4. **Quantity Validation:** Filtered **10,587 non-commercial negative quantity adjustments** (damaged goods, loss, stock audit write-offs).
5. **Non-Merchandise Codes:** Filtered administrative items (`POST`, `D`, `CR`, `BANK CHARGES`, `AMAZONFEE`).
6. **Customer Classification:** Isolated **135,037 transactions with missing CustomerIDs** as valid Guest checkouts, preserving revenue while isolating identified accounts for RFM quintiles.
7. **Cleaned Yield:** **522,710 verified transactions** generating **£10,266,018.19 in gross revenue** (Data Quality Score: **94.8 / 100**).

---

## 8. Database Schema & Dimensional Design

The database (`retailiq_db`) implements a star schema consisting of 13 tables:

```
[dim_date] (374 days)           [dim_product] (3,805 SKUs)
       │                                 │
       └───┐                         ┌───┘
           ▼                         ▼
        [fact_sales] (522,710 verified transactions)
           ▲                         ▲
       ┌───┘                         └───┐
       │                                 │
[dim_customer] (4,334 accounts)  [daily_sales] & [monthly_sales]
```

### Key Relational Tables:
1. `raw_transactions`: Staging table for raw CSV/XLSX ingestion.
2. `dim_date`: Complete calendar dimension with year, quarter, month, day, day of week, and weekend indicators.
3. `dim_product`: Active merchandise catalog with lifetime revenue, units sold, and velocity tiers.
4. `dim_customer`: Customer profiles with geography, lifetime spend, and assigned RFM segments.
5. `fact_sales`: Line-item transactional facts with unit price, quantity, line total, and dimension foreign keys.
6. `daily_sales` & `monthly_sales`: Aggregated time-series summary tables.
7. `product_metrics` & `customer_metrics`: Velocity rankings and RFM scorecards.
8. `forecast_results`: Multi-horizon ML prediction points with lower and upper confidence bounds.
9. `inventory_parameters`: Configurable replenishment attributes and stockout risk tiers.
10. `pipeline_runs`: Execution audit logs with status, timestamps, duration, and quality scores.
11. `data_quality_reports`: Historical data health JSON reports.

---

## 9. Advanced Analytical SQL Queries

RetailIQ includes `database/analytical_queries.sql`, containing 22 production-grade SQL queries demonstrating:
- **CTEs and Window Functions:** `LAG()` for Month-over-Month (MoM) revenue growth.
- **Moving Averages:** `AVG(revenue) OVER (ORDER BY date_key ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` for rolling 7-day and 30-day velocity.
- **Ranking Functions:** `DENSE_RANK() OVER (PARTITION BY country ORDER BY SUM(line_total) DESC)` for top SKUs per territory.
- **RFM Quintile Scoring:** `NTILE(5)` over recency, frequency, and monetary spend.
- **Pareto Cumulative Distribution:** Window `SUM() OVER (ORDER BY revenue DESC)` to evaluate the 80/20 product rule.
- **Basket Affinity (Self-Joins):** Identifying pairs of SKUs most frequently purchased together in the same transaction.

---

## 10. Machine Learning Demand Forecasting Engine

### Feature Engineering
Time-series features are constructed strictly without data leakage:
- **Lag Features:** Lag 1, Lag 7, Lag 14, Lag 28.
- **Rolling Statistics:** 7-day, 14-day, and 28-day rolling means and standard deviations computed on shifted values ($y_{t-1}$).
- **Calendar Signals:** Day of week, month, day of month, week of year, weekend flag, and trend index.

### Chronological Train-Test Split
- **Rule:** Never shuffle or randomly split time-series data.
- **Split:** The earliest $N - 30$ days form the training split; the final 30 calendar days form the out-of-time test evaluation set.

### Competitive Model Benchmark
Three distinct architectures are trained and evaluated:
1. **Model 1: Seasonal Naive Baseline:** Projects 7-day weekly periodicity ($y_t = y_{t-7}$).
2. **Model 2: Holt-Winters Exponential Smoothing:** Captures level, trend, and seasonal components via Statsmodels ETS.
3. **Model 3: XGBoost Regressor:** Gradient-boosted decision trees using lag, rolling, and calendar signals.

### Evaluation Metrics & Leaderboard Results
Evaluated on the out-of-time test split:

| Series | Selected Champion Model | WAPE (%) | RMSE | MAE |
| :--- | :--- | :--- | :--- | :--- |
| **Enterprise Daily Revenue (ALL)** | Seasonal Naive Baseline | **27.06%** | £28,333.26 | £14,650.75 |
| **SKU 22423 (Regency Cakestand)** | XGBoost Regressor | **52.44%** | 28.62 | 21.18 |
| **SKU 85123A (White Hanging Heart)**| Holt-Winters Exp Smoothing | **66.76%** | 121.45 | 86.87 |
| **SKU 85099B (Jumbo Bag Retrospot)** | Holt-Winters Exp Smoothing | **80.20%** | 205.57 | 134.33 |
| **SKU 47566 (Party Bunting)** | Seasonal Naive Baseline | **79.48%** | 60.37 | 24.40 |

Multi-horizon forecasts for **7, 30, and 90 days** are generated with 95% statistical confidence bounds and persisted directly to the database.

---

## 11. Inventory Optimization Engine

RetailIQ implements scientific inventory decision formulas:
- **Expected Lead-Time Demand:** $\bar{d} \times L$
- **Safety Stock:** $Z \times \sigma_d \times \sqrt{L}$ (where $Z = 1.645$ for 95% service level)
- **Reorder Point (ROP):** $\text{Lead-Time Demand} + \text{Safety Stock}$
- **Economic Order Quantity (EOQ):** $\sqrt{\frac{2 \times \text{Annual Demand} \times \text{Reorder Cost}}{\text{Holding Cost}}}$
- **Suggested Replenishment:** $\max(0, \text{Target Stock} - \text{Current Stock})$
- **Inventory Coverage:** $\frac{\text{Current Stock}}{\bar{d}}$ (in days)
- **Stockout Risk Levels:** `Critical` (below Safety Stock), `High` (below ROP), `Medium` (approaching ROP), `Low` (healthy buffer).

---

## 12. Customer Analytics & RFM Segmentation

Using the 4,334 identified accounts in the dataset, customer purchase behavior is scored using quintiles:

| Cohort | Characteristics | Revenue Share | Actionable Strategy |
| :--- | :--- | :--- | :--- |
| **Champions** | High R (recent), High F (frequent), High M (spend) | **41.2%** | VIP rewards, early product launches, advocacy incentives. |
| **Loyal Customers** | Moderate-to-high frequency and steady spend | **28.6%** | Upselling, cross-selling bundle discounts, loyalty tier points. |
| **Potential Loyalists**| Recent buyers with above-average spend | **14.8%** | Onboarding campaigns, review requests, product recommendations. |
| **At Risk** | High historical spenders with low recency | **9.1%** | Win-back email offers, reactivation surveys, exclusive discounts. |
| **Hibernating** | Low recency, low frequency, low spend | **6.3%** | Low-cost automated email reactivation or list purging. |

---

## 13. FastAPI REST Endpoints

| Category | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Health** | `/api/health` | GET | Probes system status and database connectivity. |
| **Metadata** | `/api/metadata` | GET | Returns platform version, dataset source, and model list. |
| **Dashboard** | `/api/dashboard/summary` | GET | Returns real KPIs (revenue, orders, units, AOV, repeat rate). |
| **Dashboard** | `/api/dashboard/revenue-trend` | GET | Daily revenue time series with optional date filters. |
| **Dashboard** | `/api/dashboard/top-products` | GET | Top 10 products ranked by total revenue. |
| **Dashboard** | `/api/dashboard/country-performance` | GET | Country revenue distribution and global share %. |
| **Sales** | `/api/sales` | GET | Paginated fact transactions with search and country filters. |
| **Sales** | `/api/sales/monthly` | GET | Monthly revenue, orders, quantity, and MoM growth rate. |
| **Sales** | `/api/sales/products` | GET | Product velocity catalog with search and filtering. |
| **Customers** | `/api/customers/summary` | GET | RFM segmentation summary and cohort spend share. |
| **Customers** | `/api/customers/segments` | GET | Segment descriptions and marketing recommendations. |
| **Customers** | `/api/customers/rfm` | GET | Paginated customer accounts with individual RFM metrics. |
| **Forecast** | `/api/forecast` | GET | Returns 7/30/90-day predictions with 95% confidence intervals. |
| **Forecast** | `/api/forecast/accuracy` | GET | Returns competitive model evaluation leaderboard. |
| **Forecast** | `/api/forecast/models` | GET | Lists available trained forecast targets. |
| **Inventory** | `/api/inventory/overview` | GET | Summary cards and full replenishment status ledger. |
| **Inventory** | `/api/inventory/recommendations` | GET | Products with Critical or High stockout risk. |
| **Inventory** | `/api/inventory/parameters/{sku}` | PUT | Dynamically recalculates thresholds with updated user parameters. |
| **Pipeline** | `/api/pipeline/run` | POST | Triggers manual background execution of the ETL pipeline. |
| **Pipeline** | `/api/pipeline/status` | GET | Returns latest pipeline run status and quality score. |
| **Pipeline** | `/api/pipeline/history` | GET | Returns execution audit ledger across past runs. |
| **Data** | `/api/data/upload` | POST | Uploads custom CSV/XLSX and verifies schema. |
| **Data** | `/api/data/quality-report` | GET | Returns latest data quality scorecard JSON. |

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

## 14. Frontend User Experience

The React frontend presents a bespoke dark navy enterprise SaaS design system:
1. **Executive Overview (`/`):** Top-line KPI metric cards, combined Monthly Revenue & MoM Growth chart, Geographic share bar, and Top 10 merchandise table.
2. **Sales Analytics (`/sales`):** Continuous daily revenue area chart, multi-filter transaction ledger with country dropdown, SKU search, and CSV export.
3. **Product Intelligence (`/products`):** Velocity tier categorization (High, Medium, Low Velocity), 80/20 Pareto metrics, and catalog search.
4. **Customer Insights (`/customers`):** RFM cohort comparison bar charts, strategic retention insight cards, and individual customer RFM scorecards.
5. **Demand Forecasting (`/forecast`):** Target switcher (Global Revenue vs Top SKUs), horizon selector (7D, 30D, 90D), interactive actual vs. predicted chart with 95% confidence bounds, and competitive model evaluation leaderboard.
6. **Inventory Optimization (`/inventory`):** Stockout risk ledger, coverage in days, replenishment quantity recommendations, and an interactive **Tune Parameters modal** that updates the database and recalculates safety stock in real time.
7. **Data Pipeline (`/pipeline`):** Live execution monitor, 7-stage architectural workflow diagram, execution history table, and manual "Run Pipeline" button.
8. **Data Quality (`/quality`):** 94.8/100 health scorecard with transparent mathematical scoring formula, anomaly audit counts, and links to download audit JSON or view the full HTML EDA report.
9. **Settings (`/settings`):** Database connection status, runtime environment details, and custom CSV upload form.

---

## 15. Installation & Windows Startup Instructions

### Prerequisites
- Python 3.11+
- Node.js v18+ / v20+ and npm
- Git

### Step 1: Clone the Repository
```powershell
git clone https://github.com/your-username/retailiq.git
cd retailiq
```

### Step 2: Set Up Python Backend Environment
```powershell
# Create virtual environment (optional)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Step 3: Initialize the Dataset, Database & Models
```powershell
# 1. Download official UCI dataset and convert to CSV
python scripts/download_dataset.py

# 2. Execute end-to-end ETL pipeline (Cleaning, DB loading, Quality audit)
python pipeline/run_pipeline.py

# 3. Train ML demand forecasting models (Seasonal Naive, Holt-Winters, XGBoost)
python ml/training/trainer.py

# 4. Generate standalone HTML EDA report
python pipeline/eda.py
```

### Step 4: Run the Backend API Server
```powershell
# Starts FastAPI server at http://127.0.0.1:8000
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 5: Set Up and Run the React Frontend
Open a new PowerShell terminal:
```powershell
cd frontend

# Install Node dependencies
npm install

# Start Vite development server at http://localhost:5173
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

## 16. Automated Test Suite Execution

Run all automated unit and integration tests:

```powershell
# Run backend pytest test suite
python -m pytest backend/tests/ -v
```

**Results:**
```
backend/tests/test_api.py::test_health_check PASSED                      [  5%]
backend/tests/test_api.py::test_metadata_endpoint PASSED                 [ 10%]
backend/tests/test_api.py::test_dashboard_summary PASSED                 [ 15%]
backend/tests/test_api.py::test_revenue_trend PASSED                     [ 20%]
backend/tests/test_api.py::test_top_products PASSED                      [ 25%]
backend/tests/test_api.py::test_country_performance PASSED               [ 30%]
backend/tests/test_api.py::test_monthly_sales PASSED                     [ 35%]
backend/tests/test_api.py::test_customer_summary_and_rfm PASSED          [ 40%]
backend/tests/test_api.py::test_forecast_endpoint_global PASSED          [ 45%]
backend/tests/test_api.py::test_inventory_overview_and_update PASSED     [ 50%]
backend/tests/test_api.py::test_pipeline_status PASSED                   [ 55%]
backend/tests/test_data_cleaning.py::test_duplicate_removal PASSED       [ 60%]
backend/tests/test_data_cleaning.py::test_cancellation_detection PASSED  [ 65%]
backend/tests/test_data_cleaning.py::test_invalid_unit_prices PASSED     [ 70%]
backend/tests/test_data_cleaning.py::test_revenue_calculation PASSED     [ 75%]
backend/tests/test_forecasting.py::test_chronological_splitting PASSED   [ 80%]
backend/tests/test_forecasting.py::test_forecast_metrics_calculation PASSED [ 85%]
backend/tests/test_forecasting.py::test_seasonal_naive_forecast PASSED   [ 90%]
backend/tests/test_inventory.py::test_inventory_optimizer_formulas PASSED [ 95%]
backend/tests/test_inventory.py::test_overstock_classification PASSED    [100%]
======================= 20 passed in 6.54s ========================
```

Execute frontend TypeScript and production build validation:
```powershell
cd frontend
npm run build
```
Output: `✓ built in 12.37s` (Zero compilation errors).

---

## 17. Power BI Integration Assets

RetailIQ includes dedicated Power BI artifacts in the `powerbi/` directory:
- **`powerbi/dax_measures.md`**: Complete DAX dictionary (Total Revenue, MoM Growth %, 7-Day & 30-Day Moving Averages, Repeat Customer Rate %, Pareto Cumulative Share %, Stockout Risk Flags).
- **`powerbi/dashboard_design.md`**: Visual layout specifications for 5 report pages (Executive Overview, Sales Performance, Product Intelligence, Customer Segmentation, Demand Forecasting).

---

## 18. Vercel & Production Deployment Readiness

### Frontend Deployment (Vercel)
1. Push repository to GitHub.
2. In the Vercel dashboard, import the repository and set the **Root Directory** to `frontend`.
3. Set the Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-backend-api.com`
4. Deploy. The included `frontend/vercel.json` ensures all SPA routes redirect cleanly to `/index.html`.

### Backend Hosting Requirements
Deploy the backend container (FastAPI + PostgreSQL) onto persistent infrastructure:
- **Options:** AWS ECS / App Runner, Render, Railway, DigitalOcean App Platform, or Kubernetes.
- Set `DATABASE_URL` to your production PostgreSQL connection string (`postgresql://user:pass@host:5432/retailiq_db`).

---

## 19. Technical Documentation Index

- **System Architecture & Mermaid Diagrams:** [`docs/architecture.md`](file:///E:/RetailIQ/docs/architecture.md)
- **Enterprise Data Dictionary:** [`docs/data_dictionary.md`](file:///E:/RetailIQ/docs/data_dictionary.md)
- **32-Question Technical Interview Preparation:** [`docs/interview_preparation.md`](file:///E:/RetailIQ/docs/interview_preparation.md)
- **Power BI DAX Measures:** [`powerbi/dax_measures.md`](file:///E:/RetailIQ/powerbi/dax_measures.md)
- **Power BI Dashboard Layouts:** [`powerbi/dashboard_design.md`](file:///E:/RetailIQ/powerbi/dashboard_design.md)
- **Development Status Tracker:** [`DEVELOPMENT_STATUS.md`](file:///E:/RetailIQ/DEVELOPMENT_STATUS.md)

---

## 20. Remaining Limitations & Future Roadmap

1. **Airflow DAG Portability:** While the current orchestrator (`pipeline/run_pipeline.py`) implements retries, task auditing, and 7 discrete stages, migrating to native Apache Airflow DAGs with Celery workers is planned for distributed execution.
2. **Deep Learning Forecasting:** Future enhancements include incorporating N-BEATS, Temporal Fusion Transformers (TFT), or NeuralProphet alongside XGBoost for complex holiday lead-time patterns.
3. **Multi-Warehouse Topology:** Extending the inventory engine to allocate safety stocks dynamically across regional distribution hubs.

---

## 21. License & Acknowledgments

This project is licensed under the MIT License.
Dataset provided courtesy of the **UCI Machine Learning Repository**:
*Chen, D. (2015). Online Retail. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33.*
