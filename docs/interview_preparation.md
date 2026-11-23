# RetailIQ: Technical Interview Preparation Guide
## 32 In-Depth Questions & Answers Across Modern Data Stack & Machine Learning Engineering

This guide is designed for technical interviews (Data Engineer, ML Engineer, Full-Stack Data Scientist, Backend Engineer) based directly on the architectural decisions and engineering implementations in **RetailIQ**.

---

### Category 1: Python Engineering

#### Q1: How did you ensure memory efficiency and high throughput when processing the 540k+ raw records in Python?
**Answer:**
We combined several strategies:
1. **Engine Selection & Vectorization:** Rather than iterating through rows with Python `for` loops or `apply()`, we leveraged vectorized Pandas operations backed by C-level implementations.
2. **PyArrow CSV Engine:** We utilized the `pyarrow` engine in `pd.read_csv()`, which utilizes multi-threaded columnar memory mapping, reducing read time from 30+ seconds down to under 300 milliseconds.
3. **Chunked Database Inserts:** When bulk loading into SQL (`fact_sales`), we used `chunksize=50000` to prevent memory blowups and lock escalation, batching row insertions efficiently.
4. **Data Type Casting:** String normalization and category mappings were performed in single contiguous passes, discarding intermediate large dataframes to allow garbage collection.

#### Q2: How do you handle schema drift or unexpected data types during ingestion in Python?
**Answer:**
In `pipeline/extract.py`, we implement deterministic schema validation against `EXPECTED_COLUMNS`. Before loading, the extractor performs:
- Column presence assertions (detecting missing or renamed keys).
- Type coercion with error segregation (e.g., `pd.to_datetime(errors='coerce')` to flag invalid timestamps rather than crashing silently).
- Logging an anomaly count and rejecting transactions if critical identity fields are corrupted.

---

### Category 2: SQL & Advanced Analytics

#### Q3: How did you calculate Month-over-Month (MoM) revenue growth in SQL, and how do you prevent division-by-zero errors?
**Answer:**
We utilized a Common Table Expression (CTE) and the `LAG()` window function:
```sql
WITH monthly_rev AS (
    SELECT 
        d.year_month,
        ROUND(SUM(f.line_total), 2) AS monthly_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year_month
)
SELECT 
    year_month,
    monthly_revenue,
    LAG(monthly_revenue, 1) OVER (ORDER BY year_month) AS prev_month_revenue,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY year_month)) /
        NULLIF(LAG(monthly_revenue, 1) OVER (ORDER BY year_month), 0) * 100, 
        2
    ) AS mom_growth_pct
FROM monthly_rev;
```
`NULLIF(..., 0)` safely converts zeros to `NULL`, causing the division to return `NULL` rather than raising a runtime DB error.

#### Q4: What is the difference between `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()`, and where did you use them in RetailIQ?
**Answer:**
- `ROW_NUMBER()` assigns a unique, sequential integer to every row regardless of ties (used for cumulative SKU rankings in Pareto distribution).
- `RANK()` assigns identical ranks to ties, but skips subsequent rank numbers (e.g. 1, 2, 2, 4).
- `DENSE_RANK()` assigns identical ranks to ties without skipping subsequent numbers (e.g. 1, 2, 2, 3).
In RetailIQ Query 3, we used `DENSE_RANK() OVER (PARTITION BY country ORDER BY SUM(line_total) DESC)` to reliably select the top 3 products in every country without gaps when items had identical revenues.

#### Q5: How did you compute rolling 7-day and 30-day moving averages in SQL?
**Answer:**
We used explicit physical framing in the `OVER` clause:
```sql
SELECT 
    date_key,
    revenue,
    ROUND(AVG(revenue) OVER (
        ORDER BY date_key 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_7day_avg
FROM daily_sales;
```
`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` ensures that exactly 7 discrete observations are included in the rolling window.

---

### Category 3: ETL & Data Engineering

#### Q6: How do you achieve idempotency in the RetailIQ ETL pipeline?
**Answer:**
Idempotency ensures that running the pipeline multiple times on the same input produces the exact same state without duplicate records:
1. Stage-wise table replacement or atomic upserts (`MERGE` / `ON CONFLICT DO UPDATE`).
2. Unique composite constraints on transactions: `(invoice_no, stock_code, invoice_date, quantity, unit_price)` in `fact_sales`.
3. Generating unique deterministic date keys (`dim_date`) derived directly from calendar timestamps.
4. Logging execution states in `pipeline_runs` with distinct `run_id` tracking.

#### Q7: How are cancellations and negative quantities handled during ETL?
**Answer:**
In UCI Online Retail, cancellations have invoice numbers starting with `'C'` and negative quantities.
1. We flag these via `is_cancellation = InvoiceNo.str.startswith("C")`.
2. Completed sales require `is_cancellation == False`, `Quantity > 0`, and `UnitPrice > 0`.
3. Non-cancellation negative rows (which represent stock scrap, theft, or inventory adjustments like "damaged", "lost") are isolated and excluded from commercial revenue facts.

---

### Category 4: Data Warehousing & PostgreSQL

#### Q8: Why did you choose a Star Schema over a normalized 3NF or a single wide flat table?
**Answer:**
- **Analytical Performance:** Star schemas minimize the number of joins needed for business intelligence queries compared to 3NF.
- **Simplicity for BI Tools:** Power BI, Tableau, and SQL analysts benefit from intuitive dimension-to-fact relationships.
- **Maintainability vs Flat Tables:** A single flat table repeats text descriptions and customer countries across 500,000+ rows, inflating storage and making updates inefficient. Star schema decouples `dim_product` (3,805 rows) and `dim_customer` (4,334 rows) from `fact_sales` (522,710 rows).

#### Q9: What indexes were created on `fact_sales` and why?
**Answer:**
We created single-column and composite B-tree indexes on:
- `idx_fact_sales_date` on `date_key`: Speeds up time-series filtering and rolling date joins.
- `idx_fact_sales_product` on `stock_code`: Optimizes product-level demand aggregations and inventory queries.
- `idx_fact_sales_customer` on `customer_id`: Enables instantaneous customer history lookup.
- `idx_fact_sales_country` on `country`: Accelerates geographic slice-and-dice queries.

---

### Category 5: Exploratory Data Analysis (EDA)

#### Q10: What were the most critical statistical insights discovered during EDA?
**Answer:**
1. **Severe Seasonality (Q4 Spike):** Monthly revenue remained between £500k–£700k from January to August, then surged dramatically in September (£1.0M), October (£1.07M), and November (£1.46M).
2. **Weekly Purchasing Habits:** Commercial catalog orders peaked on Thursdays and Tuesdays; Saturdays recorded virtually zero transactions, characteristic of B2B trading.
3. **Geographic Concentration:** The UK accounted for ~85.1% of revenue; top export markets were the Netherlands, Ireland (EIRE), Germany, and France.
4. **Pareto Validation:** The top 20% of merchandise SKUs drove 79.4% of total enterprise sales.

---

### Category 6: Feature Engineering for Time Series

#### Q11: How do you prevent data leakage when generating lag and rolling window features?
**Answer:**
Data leakage occurs when future information leaks into training features. To prevent this:
1. Target variables are shifted by at least 1 period (`t-1`).
2. Rolling statistics (mean, std) are computed strictly over the shifted target: `df['y'].shift(1).rolling(window=7).mean()`. This ensures that day $t$'s feature vector only contains information observable at the end of day $t-1$.
3. Feature scaling and transformations are fit strictly on training splits and applied to validation/test sets without refitting.

#### Q12: Why is continuous daily reindexing mandatory before computing time-series lags?
**Answer:**
Retail businesses often do not trade on weekends, holidays, or warehouse shutdown days. If these missing days are not explicitly reindexed, `lag_1` on Monday would mistakenly pull Friday's value (a 3-day gap), corrupting periodicity models. We reindex the timeline to daily frequency (`freq='D'`) and fill closed days with `0.0` demand.

---

### Category 7: Time-Series Demand Forecasting

#### Q13: Why is random K-Fold cross-validation strictly invalid for time-series forecasting?
**Answer:**
Random splitting violates temporal ordering. If random days from November are placed in the training set and days from August in the test set, the model trains on future data to predict the past, creating false high accuracy that fails catastrophically in production. Chronological splitting (e.g. Train: Dec 2010 – Oct 2011; Test: Nov 2011 – Dec 2011) preserves the true forward-looking prediction setting.

#### Q14: Explain the 3 models implemented in RetailIQ and their respective strengths.
**Answer:**
1. **Model 1: Seasonal Naive Baseline:** Repeats the observed value from exactly one season ago ($y_{t} = y_{t-7}$). Serves as a benchmark with zero training latency.
2. **Model 2: Holt-Winters Exponential Smoothing:** Decomposes level, trend, and weekly seasonality using smoothing parameters ($\alpha, \beta, \gamma$). Well-suited for smooth, cyclical macro demand patterns.
3. **Model 3: XGBoost Forecaster:** Gradient-boosted decision trees using multi-period lags (1, 7, 14, 28), rolling momentum statistics, and calendar attributes (day of week, month, weekend). Captures non-linear feature interactions and abrupt trend shifts.

---

### Category 8: Model Evaluation & Selection

#### Q15: Why is WAPE preferred over standard MAPE in retail demand forecasting?
**Answer:**
$\text{MAPE} = \frac{1}{n}\sum \left|\frac{y - \hat{y}}{y}\right|$. When retail sales on a given day are 0 or near 0, the denominator explodes or requires artificial epsilon offsets, distorting the metric.
$\text{WAPE} = \frac{\sum |y - \hat{y}|}{\sum y}$. WAPE weights errors by volume, ensuring high-volume days receive appropriate priority while remaining mathematically well-behaved when low-volume days have zero sales.

#### Q16: How did you calculate confidence intervals for the multi-step forecasts?
**Answer:**
Using the out-of-time residual standard error (RMSE) from the validation split:
$$\text{Lower Bound} = \max(0, \hat{y}_t - 1.96 \cdot \text{RMSE})$$
$$\text{Upper Bound} = \hat{y}_t + 1.96 \cdot \text{RMSE}$$
This provides a statistically grounded 95% confidence band for inventory managers.

---

### Category 9: Inventory Optimization

#### Q17: What is the mathematical formula for the Reorder Point (ROP)?
**Answer:**
$$\text{Reorder Point (ROP)} = \text{Expected Lead-Time Demand} + \text{Safety Stock}$$
$$\text{Expected Lead-Time Demand} = \bar{d} \times L$$
$$\text{Safety Stock} = Z \times \sigma_d \times \sqrt{L}$$
Where $\bar{d}$ is average daily demand, $L$ is supplier lead time in days, $\sigma_d$ is standard deviation of daily demand, and $Z$ is the standard normal distribution score corresponding to the target service level (e.g. $Z = 1.645$ for 95% service level).

#### Q18: How does RetailIQ classify stockout risk levels?
**Answer:**
- **Critical:** Current stock is below Safety Stock, or on-hand inventory is 0. High probability of stockout before supplier replenishment arrives.
- **High:** Current stock is below the Reorder Point. Replenishment purchase order must be placed immediately.
- **Medium:** Current stock is above ROP, but inventory coverage is less than supplier lead time.
- **Low:** Current stock is above ROP with healthy buffer coverage.

---

### Category 10: Customer Analytics & RFM

#### Q19: Explain the RFM quintile scoring methodology implemented in RetailIQ.
**Answer:**
Using Pandas `qcut()` or SQL `NTILE(5)`:
- **Recency (R):** Elapsed days since last order. Customers are ranked in ascending order (lowest days = Score 5).
- **Frequency (F):** Distinct order count. Customers are ranked in ascending order (highest orders = Score 5).
- **Monetary (M):** Total historical spend. Customers are ranked in ascending order (highest spend = Score 5).
The combined score ($R, F, M \in [1, 5]$) feeds a deterministic classification ruleset yielding cohorts: *Champions*, *Loyal Customers*, *Potential Loyalists*, *At Risk*, and *Hibernating*.

#### Q20: Why must historical customer spend be separated from Predictive Customer Lifetime Value (pCLV)?
**Answer:**
Historical spend is observed, backward-looking revenue. Representing it as forward-looking Lifetime Value can lead marketing teams to over-invest in churned high-historical-spend accounts. In RetailIQ, historical spend is clearly audited as historical revenue, while future value requires retention and churn probability modeling.

---

### Category 11: FastAPI & Backend Architecture

#### Q21: How does RetailIQ structure its FastAPI routers and dependency injection?
**Answer:**
We follow modular routing:
- `backend/app/api/` contains isolated routers for `/dashboard`, `/sales`, `/customers`, `/forecast`, `/inventory`, `/pipeline`, and `/data`.
- Database sessions are injected using FastAPI's `Depends(get_db)`, which yields a scoped SQLAlchemy session per request and guarantees `db.close()` in a `finally` block, preventing connection pooling leaks.

#### Q22: How are long-running ETL pipeline triggers handled without blocking HTTP requests?
**Answer:**
In `backend/app/api/pipeline.py`, the `POST /api/pipeline/run` endpoint utilizes FastAPI's `BackgroundTasks`. The request immediately returns a `200 OK` with status `QUEUED` and a unique `run_id`, while the orchestrator executes asynchronously in the background. The frontend polls `/api/pipeline/status` to display real-time execution telemetry.

---

### Category 12: Frontend & React Architecture

#### Q23: Why did you choose Vite + React + TypeScript + Tailwind CSS?
**Answer:**
- **Vite:** Instant Hot Module Replacement (HMR) and optimized Rollup production bundling.
- **TypeScript:** Strict type contracts with Pydantic backend models prevent runtime object shape errors.
- **Tailwind CSS:** Utility-first styling enabling a clean, bespoke Dark Navy enterprise aesthetic without heavy external component library overhead.
- **Recharts:** Composable SVG data visualizations that integrate with React state.

#### Q24: How does the React application handle network degradation or API failures?
**Answer:**
Every page implements:
1. `loading` states with `<LoadingSpinner />` to prevent layout shifts.
2. `error` capture with `<ErrorAlert />` displaying actionable error messages and retry buttons.
3. Decoupled API services in `src/services/api.ts` with Axios interceptors and configurable `VITE_API_BASE_URL`.

---

### Category 13: CI/CD & Version Control

#### Q25: What does your GitHub Actions CI workflow validate on pull requests?
**Answer:**
The workflow (`.github/workflows/ci.yml`) runs two parallel jobs:
1. `backend-test`: Spins up Ubuntu with Python 3.11, installs dependencies, and runs `pytest backend/tests/ -v` (testing endpoints, data cleaning, ML splitting, and inventory math).
2. `frontend-build`: Spins up Ubuntu with Node 20, runs `npm ci`, and executes `npm run build` (`tsc && vite build`) to guarantee type safety and bundle generation.

#### Q26: What rules did you enforce in `.gitignore`?
**Answer:**
- Exclusion of large raw datasets (`*.xlsx`, `*.csv` in `data/raw/` and `data/processed/`).
- Exclusion of database binaries (`*.db`, `retailiq.db`).
- Exclusion of local environment files (`.env`, `.env.local`).
- Exclusion of compiled ML binaries and cache (`*.pkl`, `*.joblib`, `__pycache__`).
- Exclusion of Node modules and build distributions (`node_modules/`, `dist/`).

---

### Category 14: Vercel & Production Deployment

#### Q27: How is the frontend prepared for Vercel deployment?
**Answer:**
1. **SPA Client Routing:** Configured `vercel.json` rewrites all requests `/(.*)` to `/index.html` to allow client-side React Router navigation without 404s.
2. **Dynamic Base URL:** Environment variable `VITE_API_BASE_URL` is configured in Vercel settings to target the deployed FastAPI backend.
3. **Optimized Build:** `npm run build` outputs static assets into `dist/` with chunk splitting.

#### Q28: Why should the FastAPI backend and database NOT be deployed directly onto Vercel?
**Answer:**
Vercel is a serverless frontend hosting platform optimized for static assets and short-lived Edge/Serverless functions (with execution timeout limits of 10–60 seconds). A production machine learning backend requiring persistent database connection pools, 50-second ETL pipeline executions, and in-memory XGBoost/Statsmodels training must be hosted on containerized services (e.g. AWS ECS, Render, Railway, DigitalOcean Droplet, or Kubernetes).

---

### Category 15: System Design & Scaling

#### Q29: How would you scale this architecture to 100 million transactions?
**Answer:**
1. **Ingestion & Processing:** Migrate from single-node Pandas to Apache Spark / PySpark or Polars lazy execution partitioned across nodes.
2. **Storage Layer:** Migrate to Snowflake, Google BigQuery, or Amazon Redshift using date-partitioned and product-clustered tables.
3. **Orchestration:** Transition from Python `run_pipeline.py` to Apache Airflow with Celery or Kubernetes executors.
4. **Caching:** Deploy Redis in front of FastAPI for pre-calculated dashboard metrics.

#### Q30: How do you detect and handle concept drift in the demand forecasting models?
**Answer:**
1. Log live prediction errors against observed actuals weekly.
2. Track rolling WAPE over 30-day windows.
3. Trigger automated model retraining if WAPE degrades by more than 15% relative to the validation baseline.

#### Q31: How would you test database migrations when upgrading schema in production?
**Answer:**
Using Alembic migrations:
- Run migrations against a staging replica of the production database.
- Verify backward compatibility (e.g. add new nullable columns before altering queries).
- Perform blue-green database deployments with rollback verification.

#### Q32: What makes RetailIQ stand out as an enterprise-grade portfolio platform?
**Answer:**
RetailIQ demonstrates complete full-lifecycle ownership:
- Uses official UCI raw data without fabrication.
- Implements idempotent data cleaning and star-schema dimensional modeling.
- Enforces strict chronological ML validation with zero data leakage.
- Provides scientific inventory optimization formulas (safety stock, ROP, EOQ).
- Delivers a responsive, typed React frontend backed by automated testing and CI/CD.
