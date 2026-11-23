-- =====================================================================
-- RetailIQ: Advanced Analytical SQL Query Library
-- File: database/analytical_queries.sql
-- Contains 22+ production queries demonstrating CTEs, Window Functions,
-- Ranking, Time-Series Lags, Rolling Averages, and Advanced Aggregations.
-- =====================================================================

-- ---------------------------------------------------------------------
-- QUERY 1: Month-over-Month (MoM) Revenue Growth with LAG()
-- Demonstrates: CTE, Window Function (LAG), Arithmetic Percent Change
-- ---------------------------------------------------------------------
WITH monthly_rev AS (
    SELECT 
        d.year_month,
        ROUND(SUM(f.line_total), 2) AS monthly_revenue,
        COUNT(DISTINCT f.invoice_no) AS total_orders
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year_month
)
SELECT 
    year_month,
    monthly_revenue,
    total_orders,
    LAG(monthly_revenue, 1) OVER (ORDER BY year_month) AS prev_month_revenue,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY year_month)) /
        NULLIF(LAG(monthly_revenue, 1) OVER (ORDER BY year_month), 0) * 100, 
        2
    ) AS mom_growth_pct
FROM monthly_rev
ORDER BY year_month;

-- ---------------------------------------------------------------------
-- QUERY 2: 7-Day Rolling Average Daily Revenue
-- Demonstrates: Rolling Window (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
-- ---------------------------------------------------------------------
SELECT 
    date_key,
    revenue,
    ROUND(
        AVG(revenue) OVER (
            ORDER BY date_key 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_7day_avg_revenue,
    ROUND(
        AVG(revenue) OVER (
            ORDER BY date_key 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_30day_avg_revenue
FROM daily_sales
ORDER BY date_key;

-- ---------------------------------------------------------------------
-- QUERY 3: Top 3 Products Per Country Using DENSE_RANK()
-- Demonstrates: CTE, Window Function (DENSE_RANK() PARTITION BY), Filter
-- ---------------------------------------------------------------------
WITH country_product_sales AS (
    SELECT 
        f.country,
        p.stock_code,
        p.description,
        ROUND(SUM(f.line_total), 2) AS product_revenue,
        DENSE_RANK() OVER (
            PARTITION BY f.country 
            ORDER BY SUM(f.line_total) DESC
        ) AS rank_within_country
    FROM fact_sales f
    JOIN dim_product p ON f.stock_code = p.stock_code
    GROUP BY f.country, p.stock_code, p.description
)
SELECT 
    country,
    rank_within_country,
    stock_code,
    description,
    product_revenue
FROM country_product_sales
WHERE rank_within_country <= 3
ORDER BY country, rank_within_country;

-- ---------------------------------------------------------------------
-- QUERY 4: Customer RFM Quintile Scoring via NTILE(5)
-- Demonstrates: CTE, Multiple Window NTILEs, String Concatenation
-- ---------------------------------------------------------------------
WITH customer_rfm_base AS (
    SELECT 
        customer_id,
        MIN(date_key) AS first_order_date,
        MAX(date_key) AS last_order_date,
        COUNT(DISTINCT invoice_no) AS frequency,
        ROUND(SUM(line_total), 2) AS monetary
    FROM fact_sales
    WHERE customer_id IS NOT NULL AND is_guest = 0
    GROUP BY customer_id
),
rfm_scored AS (
    SELECT 
        customer_id,
        frequency,
        monetary,
        -- Higher frequency = higher score (5 is best)
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        -- Higher monetary = higher score (5 is best)
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score,
        -- More recent date = higher score (5 is best)
        NTILE(5) OVER (ORDER BY last_order_date ASC) AS r_score
    FROM customer_rfm_base
)
SELECT 
    customer_id,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score || f_score || m_score) AS rfm_combined_code
FROM rfm_scored
ORDER BY monetary DESC
LIMIT 50;

-- ---------------------------------------------------------------------
-- QUERY 5: Cumulative Revenue and Pareto 80/20 Distribution
-- Demonstrates: Window SUM() OVER (ORDER BY), Running Totals & Percentages
-- ---------------------------------------------------------------------
WITH product_totals AS (
    SELECT 
        p.stock_code,
        p.description,
        ROUND(SUM(f.line_total), 2) AS sku_revenue
    FROM fact_sales f
    JOIN dim_product p ON f.stock_code = p.stock_code
    GROUP BY p.stock_code, p.description
),
cumulative_calc AS (
    SELECT 
        stock_code,
        description,
        sku_revenue,
        SUM(sku_revenue) OVER (ORDER BY sku_revenue DESC) AS running_cumulative_rev,
        SUM(sku_revenue) OVER () AS total_enterprise_rev,
        ROW_NUMBER() OVER (ORDER BY sku_revenue DESC) AS item_rank,
        COUNT(*) OVER () AS total_skus
    FROM product_totals
)
SELECT 
    item_rank,
    stock_code,
    description,
    sku_revenue,
    ROUND((running_cumulative_rev / total_enterprise_rev) * 100, 2) AS cumulative_rev_pct,
    ROUND((item_rank::NUMERIC / total_skus) * 100, 2) AS cumulative_sku_pct
FROM cumulative_calc
ORDER BY item_rank
LIMIT 25;

-- ---------------------------------------------------------------------
-- QUERY 6: Top 10 Customers with Revenue Contribution %
-- Demonstrates: Window SUM() Grand Total, Percentage Contribution
-- ---------------------------------------------------------------------
SELECT 
    customer_id,
    country,
    order_count,
    total_spend,
    ROUND(
        (total_spend / SUM(total_spend) OVER ()) * 100, 
        3
    ) AS contribution_pct_of_total
FROM customer_metrics
ORDER BY total_spend DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- QUERY 7: Products with Declining Velocity (Quarterly Trend Analysis)
-- Demonstrates: PIVOT via Conditional Aggregation, MoM/QoQ Velocity Drop
-- ---------------------------------------------------------------------
WITH quarterly_demand AS (
    SELECT 
        f.stock_code,
        p.description,
        d.quarter_name,
        SUM(f.quantity) AS units_sold
    FROM fact_sales f
    JOIN dim_product p ON f.stock_code = p.stock_code
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY f.stock_code, p.description, d.quarter_name
),
quarter_matrix AS (
    SELECT 
        stock_code,
        description,
        COALESCE(SUM(CASE WHEN quarter_name = '2011-Q2' THEN units_sold ELSE 0 END), 0) AS q2_units,
        COALESCE(SUM(CASE WHEN quarter_name = '2011-Q3' THEN units_sold ELSE 0 END), 0) AS q3_units
    FROM quarterly_demand
    GROUP BY stock_code, description
)
SELECT 
    stock_code,
    description,
    q2_units,
    q3_units,
    (q3_units - q2_units) AS unit_difference,
    ROUND(((q3_units - q2_units)::NUMERIC / NULLIF(q2_units, 0)) * 100, 2) AS pct_change
FROM quarter_matrix
WHERE q2_units > 100 AND q3_units < q2_units
ORDER BY unit_difference ASC
LIMIT 20;

-- ---------------------------------------------------------------------
-- QUERY 8: High Value Orders (HAVING and Subqueries)
-- Demonstrates: GROUP BY, HAVING, Subquery filtering
-- ---------------------------------------------------------------------
SELECT 
    invoice_no,
    country,
    COUNT(DISTINCT stock_code) AS distinct_items,
    SUM(quantity) AS total_units,
    ROUND(SUM(line_total), 2) AS basket_value
FROM fact_sales
GROUP BY invoice_no, country
HAVING SUM(line_total) > (
    SELECT AVG(daily_revenue) * 0.10 FROM (
        SELECT SUM(line_total) AS daily_revenue FROM fact_sales GROUP BY date_key
    ) sub
)
ORDER BY basket_value DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- QUERY 9: Weekend vs Weekday Shopping Comparison
-- Demonstrates: CASE Statement aggregation, ratio calculation
-- ---------------------------------------------------------------------
SELECT 
    CASE WHEN d.is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(DISTINCT f.invoice_no) AS total_orders,
    SUM(f.quantity) AS total_units_sold,
    ROUND(SUM(f.line_total), 2) AS total_revenue,
    ROUND(AVG(f.line_total), 2) AS avg_item_spend,
    ROUND(SUM(f.line_total) / COUNT(DISTINCT f.invoice_no), 2) AS avg_basket_size
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY CASE WHEN d.is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END;

-- ---------------------------------------------------------------------
-- QUERY 10: Repeat Customer Order Intervals (LEAD/LAG Difference)
-- Demonstrates: LAG across partitioned customer orders to measure inter-purchase cycle
-- ---------------------------------------------------------------------
WITH customer_orders AS (
    SELECT DISTINCT
        customer_id,
        invoice_no,
        date_key
    FROM fact_sales
    WHERE customer_id IS NOT NULL AND is_guest = 0
),
order_intervals AS (
    SELECT 
        customer_id,
        invoice_no,
        date_key,
        LAG(date_key, 1) OVER (
            PARTITION BY customer_id 
            ORDER BY date_key
        ) AS previous_order_date
    FROM customer_orders
)
SELECT 
    customer_id,
    ROUND(AVG(date_key - previous_order_date), 1) AS avg_days_between_orders,
    COUNT(invoice_no) AS repeat_order_count
FROM order_intervals
WHERE previous_order_date IS NOT NULL
GROUP BY customer_id
HAVING COUNT(invoice_no) >= 3
ORDER BY avg_days_between_orders ASC
LIMIT 20;

-- ---------------------------------------------------------------------
-- QUERY 11: Stockout Risk Identification (Cross Joining Inventory Parameters)
-- Demonstrates: LEFT JOIN, Multi-factor risk scoring
-- ---------------------------------------------------------------------
SELECT 
    p.stock_code,
    p.description,
    i.current_stock,
    i.reorder_point,
    i.expected_lead_time_demand,
    i.safety_stock,
    i.suggested_reorder_qty,
    i.stockout_risk_level
FROM inventory_parameters i
JOIN dim_product p ON i.stock_code = p.stock_code
WHERE i.stockout_risk_level IN ('Critical', 'High')
ORDER BY i.current_stock ASC;

-- ---------------------------------------------------------------------
-- QUERY 12: Monthly Active Customers (MAC) & Cohort Sizing
-- Demonstrates: COUNT(DISTINCT) by period and cohort
-- ---------------------------------------------------------------------
SELECT 
    d.year_month,
    COUNT(DISTINCT f.customer_id) AS identified_active_customers,
    COUNT(DISTINCT CASE WHEN f.is_guest = 1 THEN f.invoice_no END) AS guest_order_count,
    ROUND(SUM(f.line_total), 2) AS monthly_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year_month
ORDER BY d.year_month;

-- ---------------------------------------------------------------------
-- QUERY 13: Top Revenue Country Rank & Cumulative Revenue Contribution
-- Demonstrates: DENSE_RANK() with running percentage of global revenue
-- ---------------------------------------------------------------------
WITH country_totals AS (
    SELECT 
        country,
        ROUND(SUM(line_total), 2) AS total_country_rev,
        COUNT(DISTINCT invoice_no) AS orders
    FROM fact_sales
    GROUP BY country
)
SELECT 
    DENSE_RANK() OVER (ORDER BY total_country_rev DESC) AS revenue_rank,
    country,
    total_country_rev,
    orders,
    ROUND((total_country_rev / SUM(total_country_rev) OVER ()) * 100, 2) AS global_share_pct
FROM country_totals
ORDER BY revenue_rank
LIMIT 15;

-- ---------------------------------------------------------------------
-- QUERY 14: Products with Highest Demand Volatility (StdDev & Variance)
-- Demonstrates: Statistical window metrics over daily product sales
-- ---------------------------------------------------------------------
WITH daily_prod_units AS (
    SELECT 
        stock_code,
        date_key,
        SUM(quantity) AS daily_qty
    FROM fact_sales
    GROUP BY stock_code, date_key
)
SELECT 
    d.stock_code,
    p.description,
    COUNT(d.date_key) AS active_days,
    ROUND(AVG(d.daily_qty), 2) AS mean_daily_qty,
    ROUND(STDDEV(d.daily_qty), 2) AS stddev_daily_qty
FROM daily_prod_units d
JOIN dim_product p ON d.stock_code = p.stock_code
GROUP BY d.stock_code, p.description
HAVING COUNT(d.date_key) > 50
ORDER BY stddev_daily_qty DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- QUERY 15: Cross-Selling Affinity (Products Purchased in the Same Basket)
-- Demonstrates: Self JOIN on InvoiceNo, Pair Frequency
-- ---------------------------------------------------------------------
SELECT 
    a.stock_code AS item_a,
    b.stock_code AS item_b,
    COUNT(DISTINCT a.invoice_no) AS times_bought_together
FROM fact_sales a
JOIN fact_sales b ON a.invoice_no = b.invoice_no AND a.stock_code < b.stock_code
GROUP BY a.stock_code, b.stock_code
HAVING COUNT(DISTINCT a.invoice_no) >= 50
ORDER BY times_bought_together DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- QUERY 16: Forecast Accuracy Evaluation Summary by Horizon
-- Demonstrates: Aggregate evaluation metrics across 7, 30, and 90 day horizons
-- ---------------------------------------------------------------------
SELECT 
    target_type,
    model_name,
    horizon_days,
    ROUND(AVG(mae), 4) AS avg_mae,
    ROUND(AVG(rmse), 4) AS avg_rmse,
    ROUND(AVG(mape), 4) AS avg_mape,
    ROUND(AVG(wape), 4) AS avg_wape,
    COUNT(*) AS prediction_points
FROM forecast_results
GROUP BY target_type, model_name, horizon_days
ORDER BY target_type, horizon_days, avg_wape ASC;

-- ---------------------------------------------------------------------
-- QUERY 17: Inactive Customers (Dormancy / Churn Risk Window)
-- Demonstrates: Subquery with Date difference and segmentation
-- ---------------------------------------------------------------------
SELECT 
    customer_id,
    country,
    total_spend,
    order_count,
    recency_days,
    segment
FROM customer_metrics
WHERE recency_days > 180 AND total_spend > 500
ORDER BY total_spend DESC
LIMIT 25;

-- ---------------------------------------------------------------------
-- QUERY 18: Peak Order Hours by Day of Week
-- Demonstrates: Multi-dimensional GROUP BY with ROW_NUMBER ranking
-- ---------------------------------------------------------------------
WITH hourly_rankings AS (
    SELECT 
        d.day_name,
        d.day_of_week,
        EXTRACT(HOUR FROM f.invoice_date) AS order_hour,
        COUNT(DISTINCT f.invoice_no) AS hourly_orders,
        ROW_NUMBER() OVER (
            PARTITION BY d.day_of_week 
            ORDER BY COUNT(DISTINCT f.invoice_no) DESC
        ) AS rank_in_day
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.day_name, d.day_of_week, EXTRACT(HOUR FROM f.invoice_date)
)
SELECT 
    day_name,
    order_hour,
    hourly_orders
FROM hourly_rankings
WHERE rank_in_day = 1
ORDER BY day_of_week;

-- ---------------------------------------------------------------------
-- QUERY 19: Customers with Single High-Value Purchase (One-Hit Wonders)
-- Demonstrates: HAVING filter on order count with high total spend
-- ---------------------------------------------------------------------
SELECT 
    customer_id,
    country,
    total_spend,
    first_order_date
FROM customer_metrics
WHERE order_count = 1 AND total_spend > 1500
ORDER BY total_spend DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- QUERY 20: Product Lifecycle - First vs Most Recent Purchase Velocity
-- Demonstrates: Lifespan in days and overall turnover
-- ---------------------------------------------------------------------
SELECT 
    stock_code,
    description,
    first_sold_date,
    last_sold_date,
    (last_sold_date::DATE - first_sold_date::DATE) AS catalog_lifespan_days,
    total_revenue,
    total_quantity
FROM product_metrics
WHERE (last_sold_date::DATE - first_sold_date::DATE) > 100
ORDER BY total_revenue DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- QUERY 21: Daily Orders and Revenue Variance Against 30-Day Moving Mean
-- Demonstrates: Dynamic Moving Z-Score / Deviation Flagging
-- ---------------------------------------------------------------------
WITH daily_stats AS (
    SELECT 
        date_key,
        revenue,
        AVG(revenue) OVER (ORDER BY date_key ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS rolling_mean_30,
        STDDEV(revenue) OVER (ORDER BY date_key ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS rolling_std_30
    FROM daily_sales
)
SELECT 
    date_key,
    revenue,
    ROUND(rolling_mean_30, 2) AS baseline_mean,
    ROUND((revenue - rolling_mean_30) / NULLIF(rolling_std_30, 0), 2) AS revenue_z_score
FROM daily_stats
WHERE rolling_std_30 IS NOT NULL
ORDER BY ABS((revenue - rolling_mean_30) / NULLIF(rolling_std_30, 0)) DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- QUERY 22: Data Pipeline Run Health and Success Rate
-- Demonstrates: Aggregated telemetry on ETL runs
-- ---------------------------------------------------------------------
SELECT 
    pipeline_name,
    status,
    COUNT(*) AS total_runs,
    ROUND(AVG(execution_duration_sec), 2) AS avg_duration_seconds,
    ROUND(AVG(data_quality_score), 1) AS avg_quality_score,
    MAX(started_at) AS most_recent_execution
FROM pipeline_runs
GROUP BY pipeline_name, status
ORDER BY most_recent_execution DESC;
