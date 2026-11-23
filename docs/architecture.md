# RetailIQ: System Architecture & Technical Topology

RetailIQ is an end-to-end Enterprise Retail Intelligence and Demand Forecasting Platform. This document outlines the end-to-end data engineering, machine learning, API, and frontend architectures.

---

## 1. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Data_Ingestion_Engineering ["Data Ingestion & Engineering Pipeline"]
        UCI["Official UCI Online Retail Dataset\n(541,909 raw records)"] --> Extractor["pipeline/extract.py\nSchema Validation & Extraction"]
        Extractor --> Cleaner["pipeline/transform.py\nDeduplication, Cancellation Flagging,\nZero-Price Filtering & Revenue Calc"]
        Cleaner --> Validator["pipeline/data_quality.py\nHealth Scorecard & Anomaly Checks"]
        Cleaner --> Aggregator["Dimensional Aggregations\n(Daily, Monthly, Product, Customer)"]
    end

    subgraph Database_Layer ["Relational Analytical Store (retailiq_db)"]
        Aggregator --> StarSchema["Star-Schema Warehouse\n- fact_sales (522,710 records)\n- dim_date (374 days)\n- dim_product (3,805 SKUs)\n- dim_customer (4,334 accounts)\n- daily_sales & monthly_sales"]
        StarSchema --> SQLViews["Analytical SQL Views\n- v_revenue_by_month\n- v_top_performing_products\n- v_repeat_customer_rate\n- v_product_demand_trends"]
    end

    subgraph ML_Analytics_Engines ["Machine Learning & Decision Engines"]
        StarSchema --> FeatBuilder["ml/features/builder.py\nLags (1,7,14,28), Rolling Means (7,14,28),\nCalendar & Trend Variables"]
        FeatBuilder --> TrainSplit["Chronological Split (Zero Leakage)\nTrain (Earlier) / Test (Last 30 Days)"]
        TrainSplit --> Model1["Model 1: Seasonal Naive Baseline"]
        TrainSplit --> Model2["Model 2: Holt-Winters Exp Smoothing"]
        TrainSplit --> Model3["Model 3: XGBoost ML Forecaster"]
        Model1 & Model2 & Model3 --> Evaluator["ml/evaluation/metrics.py\nMAE, RMSE, MAPE, WAPE Leaderboard"]
        Evaluator --> Champion["Champion Model Selection\nMulti-Horizon Forecasts (7D, 30D, 90D)"]
        Champion --> ForecastTable["forecast_results (Database)"]
        StarSchema --> InventoryEng["backend/app/inventory/optimizer.py\nSafety Stock, Lead Time Demand, ROP, EOQ"]
        StarSchema --> RFMEng["backend/app/analytics/rfm.py\nQuintile RFM Scoring & Segmentation"]
    end

    subgraph Backend_Gateway ["FastAPI Application Gateway (:8000)"]
        StarSchema & ForecastTable & InventoryEng & RFMEng --> APIRouters["FastAPI Modular Routers\n/api/dashboard\n/api/sales\n/api/customers\n/api/forecast\n/api/inventory\n/api/pipeline\n/api/data"]
    end

    subgraph Frontend_Presentation ["React 18 / TypeScript Enterprise UI (:5173)"]
        APIRouters --> ReactApp["React 18 + Tailwind CSS + Recharts\n- Executive Overview\n- Sales Ledger\n- Product Velocity\n- Customer Insights\n- Demand Forecasting\n- Inventory Optimization\n- Pipeline Monitor\n- Data Quality Health"]
    end
```

---

## 2. Database Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    dim_date ||--o{ fact_sales : "dates"
    dim_product ||--o{ fact_sales : "contains"
    dim_customer ||--o{ fact_sales : "places"
    dim_product ||--|| inventory_parameters : "configured_by"
    dim_product ||--|| product_metrics : "summarized_by"
    dim_date ||--|| daily_sales : "aggregated_as"

    dim_date {
        date date_key PK
        int year
        int quarter
        int month
        string month_name
        string year_month
        int day_of_week
        int is_weekend
    }

    dim_product {
        string stock_code PK
        string description
        numeric avg_unit_price
        numeric total_lifetime_revenue
        bigint total_lifetime_quantity
    }

    dim_customer {
        string customer_id PK
        string country
        timestamp first_order_date
        timestamp last_order_date
        int total_orders
        numeric total_spend
        string rfm_segment
    }

    fact_sales {
        bigint sale_id PK
        string invoice_no
        string stock_code FK
        string customer_id FK
        date date_key FK
        timestamp invoice_date
        int quantity
        numeric unit_price
        numeric line_total
        string country
        int is_guest
    }

    daily_sales {
        date date_key PK
        numeric revenue
        int order_count
        bigint quantity_sold
        int unique_customers
        numeric avg_order_value
    }

    inventory_parameters {
        string stock_code PK
        int current_stock
        int lead_time_days
        numeric service_level_pct
        numeric expected_lead_time_demand
        int safety_stock
        int reorder_point
        int suggested_reorder_qty
        numeric inventory_coverage_days
        string stockout_risk_level
    }

    forecast_results {
        bigint forecast_id PK
        string target_type
        string target_identifier
        string model_name
        int horizon_days
        date forecast_date
        numeric predicted_value
        numeric lower_bound
        numeric upper_bound
        numeric wape
    }
```

---

## 3. Time-Series Feature Engineering Architecture

To guarantee strict zero-data leakage, the feature generation pipeline employs the following architecture:

```
[Raw Historical Timeline]
        │
        ▼
[Continuous Reindexing (fills zero-sales closed days with 0.0)]
        │
        ▼
[Shift Target by 1 (y_t-1)]
  ├── Lags: Lag 1, Lag 7, Lag 14, Lag 28
  ├── Rolling Windows: Mean 7, Mean 14, Mean 28, Std 7, Std 14, Std 28
  └── Calendar Signals: Day of Week, Month, Week of Year, Weekend Flag, Trend Index
        │
        ▼
[Chronological Train / Test Split]
  ├── Train: First N - 30 days
  └── Out-of-Time Test: Last 30 days
```

---

## 4. Multi-Horizon Recursive Forecasting Engine

```mermaid
sequenceDiagram
    participant User as Frontend Client
    participant API as FastAPI (/api/forecast)
    participant Model as Champion Model (XGBoost/ExpSmooth)
    participant History as Historical Series Cache

    User->>API: Request 30-Day Forecast (Target: '22423')
    API->>History: Query Last 60 Days Observed Demand
    API->>Model: Execute Recursive Multi-Step Prediction
    loop 30 Forecast Days
        Model->>Model: Compute Lags (1, 7, 14, 28) from Prior Steps
        Model->>Model: Compute Rolling Mean & Std (7, 14, 28)
        Model->>Model: Inject Calendar Signals (DayOfWeek, Weekend)
        Model->>Model: Predict Day t+k
    end
    API->>API: Calculate 95% Confidence Intervals (+- 1.96 * RMSE)
    API-->>User: Return Forecast Points, Metrics & History
```

---

## 5. Deployment Topology

```mermaid
flowchart LR
    subgraph Client_Tier ["Client Browser"]
        Browser["Enterprise Browser"]
    end

    subgraph Frontend_Hosting ["Frontend (Vercel CDN)"]
        VercelEdge["Vercel Edge Network\nStatic Vite SPA (dist/)\nAutomatic HTTPS & Brotli"]
    end

    subgraph Backend_Hosting ["Backend (Docker / VPS / Cloud VM)"]
        FastAPI_Svc["FastAPI Python 3.11+\nUvicorn ASGI Workers\nGunicorn Process Manager"]
        Orchestrator["ETL Orchestrator & ML Trainer"]
    end

    subgraph Storage_Tier ["Database & Cache"]
        PostgresDB["Managed PostgreSQL 15+\nStar Schema & Relational Views"]
    end

    Browser --> VercelEdge
    VercelEdge --> Browser
    Browser -- "API Calls (HTTPS /api/*)" --> FastAPI_Svc
    FastAPI_Svc <--> PostgresDB
    Orchestrator <--> PostgresDB
```
