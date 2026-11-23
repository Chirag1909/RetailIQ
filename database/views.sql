-- =====================================================================
-- RetailIQ: Analytical SQL Views (PostgreSQL & ANSI Standard)
-- =====================================================================

-- 1. View: Revenue by Month
DROP VIEW IF EXISTS v_revenue_by_month CASCADE;
CREATE VIEW v_revenue_by_month AS
SELECT 
    d.year_month,
    d.year,
    d.month_name,
    COUNT(DISTINCT f.invoice_no) AS total_orders,
    SUM(f.quantity) AS total_units_sold,
    ROUND(SUM(f.line_total), 2) AS total_revenue,
    ROUND(AVG(f.line_total), 2) AS avg_item_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year_month, d.year, d.month_name;

-- 2. View: Revenue by Product
DROP VIEW IF EXISTS v_revenue_by_product CASCADE;
CREATE VIEW v_revenue_by_product AS
SELECT 
    p.stock_code,
    p.description,
    COUNT(DISTINCT f.invoice_no) AS orders_count,
    SUM(f.quantity) AS total_units_sold,
    ROUND(SUM(f.line_total), 2) AS total_revenue,
    ROUND(AVG(f.unit_price), 2) AS avg_price
FROM fact_sales f
JOIN dim_product p ON f.stock_code = p.stock_code
GROUP BY p.stock_code, p.description;

-- 3. View: Revenue by Country
DROP VIEW IF EXISTS v_revenue_by_country CASCADE;
CREATE VIEW v_revenue_by_country AS
SELECT 
    f.country,
    COUNT(DISTINCT f.invoice_no) AS total_orders,
    COUNT(DISTINCT f.customer_id) AS total_customers,
    SUM(f.quantity) AS total_units_sold,
    ROUND(SUM(f.line_total), 2) AS total_revenue,
    ROUND(SUM(f.line_total) / NULLIF(COUNT(DISTINCT f.invoice_no), 0), 2) AS avg_order_value
FROM fact_sales f
GROUP BY f.country;

-- 4. View: Product Demand Trends (Rolling 30-day velocity indicator)
DROP VIEW IF EXISTS v_product_demand_trends CASCADE;
CREATE VIEW v_product_demand_trends AS
SELECT 
    f.stock_code,
    p.description,
    d.year_month,
    SUM(f.quantity) AS monthly_units_sold,
    ROUND(SUM(f.line_total), 2) AS monthly_revenue
FROM fact_sales f
JOIN dim_product p ON f.stock_code = p.stock_code
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY f.stock_code, p.description, d.year_month;

-- 5. View: Customer Purchase Frequency
DROP VIEW IF EXISTS v_customer_purchase_frequency CASCADE;
CREATE VIEW v_customer_purchase_frequency AS
SELECT 
    customer_id,
    country,
    COUNT(DISTINCT invoice_no) AS total_purchases,
    SUM(line_total) AS total_spend,
    ROUND(AVG(line_total), 2) AS avg_line_value,
    MIN(invoice_date) AS first_purchase_date,
    MAX(invoice_date) AS last_purchase_date
FROM fact_sales
WHERE customer_id IS NOT NULL AND is_guest = 0
GROUP BY customer_id, country;

-- 6. View: Average Order Value (AOV) by Period
DROP VIEW IF EXISTS v_average_order_value CASCADE;
CREATE VIEW v_average_order_value AS
SELECT 
    d.year_month,
    COUNT(DISTINCT f.invoice_no) AS total_orders,
    ROUND(SUM(f.line_total), 2) AS gross_revenue,
    ROUND(SUM(f.line_total) / NULLIF(COUNT(DISTINCT f.invoice_no), 0), 2) AS average_order_value
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year_month;

-- 7. View: Monthly Growth (MoM with LAG Window Function)
DROP VIEW IF EXISTS v_monthly_growth CASCADE;
CREATE VIEW v_monthly_growth AS
WITH monthly_summary AS (
    SELECT 
        d.year_month,
        ROUND(SUM(f.line_total), 2) AS revenue,
        COUNT(DISTINCT f.invoice_no) AS orders
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year_month
)
SELECT 
    year_month,
    revenue,
    orders,
    LAG(revenue, 1) OVER (ORDER BY year_month) AS previous_month_revenue,
    ROUND(
        (revenue - LAG(revenue, 1) OVER (ORDER BY year_month)) / 
        NULLIF(LAG(revenue, 1) OVER (ORDER BY year_month), 0) * 100, 
        2
    ) AS mom_growth_pct
FROM monthly_summary;

-- 8. View: Repeat Customer Rate
DROP VIEW IF EXISTS v_repeat_customer_rate CASCADE;
CREATE VIEW v_repeat_customer_rate AS
WITH customer_order_counts AS (
    SELECT 
        customer_id,
        COUNT(DISTINCT invoice_no) AS order_count
    FROM fact_sales
    WHERE customer_id IS NOT NULL AND is_guest = 0
    GROUP BY customer_id
)
SELECT 
    COUNT(*) AS total_customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(
        SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 
        2
    ) AS repeat_customer_percentage
FROM customer_order_counts;

-- 9. View: Top Performing Products (with Revenue Rank)
DROP VIEW IF EXISTS v_top_performing_products CASCADE;
CREATE VIEW v_top_performing_products AS
SELECT 
    p.stock_code,
    p.description,
    ROUND(SUM(f.line_total), 2) AS total_revenue,
    SUM(f.quantity) AS total_units,
    DENSE_RANK() OVER (ORDER BY SUM(f.line_total) DESC) AS revenue_rank
FROM fact_sales f
JOIN dim_product p ON f.stock_code = p.stock_code
GROUP BY p.stock_code, p.description;
