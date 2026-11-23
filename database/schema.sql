-- =====================================================================
-- RetailIQ: Analytical Star-Schema Relational DDL (PostgreSQL & ANSI SQL)
-- Database: retailiq_db
-- =====================================================================

-- Drop tables if needed in dependency order
DROP TABLE IF EXISTS forecast_results CASCADE;
DROP TABLE IF EXISTS inventory_parameters CASCADE;
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS daily_sales CASCADE;
DROP TABLE IF EXISTS monthly_sales CASCADE;
DROP TABLE IF EXISTS customer_metrics CASCADE;
DROP TABLE IF EXISTS product_metrics CASCADE;
DROP TABLE IF EXISTS pipeline_runs CASCADE;
DROP TABLE IF EXISTS data_quality_reports CASCADE;
DROP TABLE IF EXISTS raw_transactions CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- 1. RAW TRANSACTIONS (Ingestion Staging)
CREATE TABLE raw_transactions (
    raw_id BIGSERIAL PRIMARY KEY,
    invoice_no VARCHAR(64) NOT NULL,
    stock_code VARCHAR(64) NOT NULL,
    description TEXT,
    quantity INTEGER,
    invoice_date TIMESTAMP,
    unit_price NUMERIC(12, 4),
    customer_id VARCHAR(64),
    country VARCHAR(100),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_raw_invoice ON raw_transactions(invoice_no);
CREATE INDEX idx_raw_date ON raw_transactions(invoice_date);

-- 2. DIMENSION: DATE (Temporal Dimension)
CREATE TABLE dim_date (
    date_key DATE PRIMARY KEY,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend INTEGER NOT NULL DEFAULT 0,
    quarter_name VARCHAR(10) NOT NULL
);

CREATE INDEX idx_dim_date_ym ON dim_date(year_month);

-- 3. DIMENSION: PRODUCT (Catalog & Categorization)
CREATE TABLE dim_product (
    stock_code VARCHAR(64) PRIMARY KEY,
    description TEXT NOT NULL,
    avg_unit_price NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_lifetime_revenue NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    total_lifetime_quantity BIGINT NOT NULL DEFAULT 0,
    first_sold_date TIMESTAMP,
    last_sold_date TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_prod_desc ON dim_product(description);

-- 4. DIMENSION: CUSTOMER (Account Profiles & Geography)
CREATE TABLE dim_customer (
    customer_id VARCHAR(64) PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    first_order_date TIMESTAMP,
    last_order_date TIMESTAMP,
    total_orders INTEGER NOT NULL DEFAULT 0,
    total_spend NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    rfm_recency INTEGER,
    rfm_frequency INTEGER,
    rfm_monetary NUMERIC(14, 2),
    rfm_segment VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_cust_country ON dim_customer(country);
CREATE INDEX idx_dim_cust_segment ON dim_customer(rfm_segment);

-- 5. FACT TABLE: SALES TRANSACTIONS
CREATE TABLE fact_sales (
    sale_id BIGSERIAL PRIMARY KEY,
    invoice_no VARCHAR(64) NOT NULL,
    stock_code VARCHAR(64) NOT NULL REFERENCES dim_product(stock_code),
    customer_id VARCHAR(64),
    date_key DATE NOT NULL REFERENCES dim_date(date_key),
    invoice_date TIMESTAMP NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 4) NOT NULL CHECK (unit_price > 0),
    line_total NUMERIC(14, 2) NOT NULL CHECK (line_total >= 0),
    country VARCHAR(100) NOT NULL,
    is_guest INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sale_line UNIQUE (invoice_no, stock_code, invoice_date, quantity, unit_price)
);

CREATE INDEX idx_fact_sales_date ON fact_sales(date_key);
CREATE INDEX idx_fact_sales_product ON fact_sales(stock_code);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_country ON fact_sales(country);

-- 6. AGGREGATE: DAILY SALES
CREATE TABLE daily_sales (
    date_key DATE PRIMARY KEY REFERENCES dim_date(date_key),
    revenue NUMERIC(14, 2) NOT NULL,
    order_count INTEGER NOT NULL,
    quantity_sold BIGINT NOT NULL,
    unique_customers INTEGER NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. AGGREGATE: MONTHLY SALES
CREATE TABLE monthly_sales (
    year_month VARCHAR(7) PRIMARY KEY,
    revenue NUMERIC(14, 2) NOT NULL,
    order_count INTEGER NOT NULL,
    quantity_sold BIGINT NOT NULL,
    unique_customers INTEGER NOT NULL,
    mom_growth_pct NUMERIC(8, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. PRODUCT METRICS
CREATE TABLE product_metrics (
    stock_code VARCHAR(64) PRIMARY KEY REFERENCES dim_product(stock_code),
    description TEXT NOT NULL,
    total_revenue NUMERIC(14, 2) NOT NULL,
    total_quantity BIGINT NOT NULL,
    order_count INTEGER NOT NULL,
    avg_unit_price NUMERIC(12, 2) NOT NULL,
    revenue_rank INTEGER,
    demand_velocity_category VARCHAR(32),
    first_sold_date TIMESTAMP,
    last_sold_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prod_metrics_rev ON product_metrics(total_revenue DESC);

-- 9. CUSTOMER METRICS
CREATE TABLE customer_metrics (
    customer_id VARCHAR(64) PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    first_order_date TIMESTAMP,
    last_order_date TIMESTAMP,
    order_count INTEGER NOT NULL,
    total_spend NUMERIC(14, 2) NOT NULL,
    total_units BIGINT NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    recency_days INTEGER NOT NULL,
    rfm_score VARCHAR(10),
    segment VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cust_metrics_spend ON customer_metrics(total_spend DESC);

-- 10. FORECAST RESULTS
CREATE TABLE forecast_results (
    forecast_id BIGSERIAL PRIMARY KEY,
    target_type VARCHAR(32) NOT NULL, -- 'GLOBAL_REVENUE' or 'PRODUCT_DEMAND'
    target_identifier VARCHAR(64) NOT NULL, -- 'ALL' or stock_code
    model_name VARCHAR(64) NOT NULL,
    horizon_days INTEGER NOT NULL, -- 7, 30, 90
    forecast_date DATE NOT NULL,
    predicted_value NUMERIC(14, 2) NOT NULL,
    lower_bound NUMERIC(14, 2),
    upper_bound NUMERIC(14, 2),
    mae NUMERIC(12, 4),
    rmse NUMERIC(12, 4),
    mape NUMERIC(8, 4),
    wape NUMERIC(8, 4),
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_forecast_target ON forecast_results(target_type, target_identifier, horizon_days);
CREATE INDEX idx_forecast_date ON forecast_results(forecast_date);

-- 11. INVENTORY PARAMETERS & RECOMMENDATIONS
CREATE TABLE inventory_parameters (
    stock_code VARCHAR(64) PRIMARY KEY REFERENCES dim_product(stock_code),
    current_stock INTEGER NOT NULL DEFAULT 100,
    lead_time_days INTEGER NOT NULL DEFAULT 14,
    service_level_pct NUMERIC(5, 2) NOT NULL DEFAULT 95.0,
    holding_cost NUMERIC(8, 2) NOT NULL DEFAULT 1.50,
    reorder_cost NUMERIC(8, 2) NOT NULL DEFAULT 25.00,
    expected_lead_time_demand NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    safety_stock INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL DEFAULT 0,
    suggested_reorder_qty INTEGER NOT NULL DEFAULT 0,
    inventory_coverage_days NUMERIC(8, 1) NOT NULL DEFAULT 0.0,
    stockout_risk_level VARCHAR(20) NOT NULL DEFAULT 'Low', -- Critical, High, Medium, Low
    overstock_risk_level VARCHAR(20) NOT NULL DEFAULT 'Low',
    last_evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. PIPELINE EXECUTION AUDIT RUNS
CREATE TABLE pipeline_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    pipeline_name VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL, -- 'SUCCESS', 'FAILED', 'RUNNING'
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    records_extracted INTEGER DEFAULT 0,
    records_cleaned INTEGER DEFAULT 0,
    records_loaded INTEGER DEFAULT 0,
    data_quality_score NUMERIC(5, 2),
    execution_duration_sec NUMERIC(10, 2),
    error_message TEXT,
    triggered_by VARCHAR(64) DEFAULT 'SYSTEM'
);

CREATE INDEX idx_pipeline_started ON pipeline_runs(started_at DESC);

-- 13. DATA QUALITY REPORTS
CREATE TABLE data_quality_reports (
    report_id VARCHAR(64) PRIMARY KEY,
    generated_at TIMESTAMP NOT NULL,
    overall_quality_score NUMERIC(5, 2) NOT NULL,
    status VARCHAR(32) NOT NULL,
    raw_record_count INTEGER NOT NULL,
    cleaned_record_count INTEGER NOT NULL,
    retention_rate_pct NUMERIC(5, 2) NOT NULL,
    duplicate_records INTEGER NOT NULL,
    missing_customer_ids INTEGER NOT NULL,
    cancellations_detected INTEGER NOT NULL,
    report_json TEXT NOT NULL
);
