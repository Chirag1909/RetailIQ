"""
RetailIQ - Analytical SQL Queries & Views Validation Script
Executes analytical views and benchmark queries against the live database schema.
"""

import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
from sqlalchemy import text
from backend.app.database.session import engine

queries = [
    ("View: Revenue by Month", "SELECT * FROM v_revenue_by_month LIMIT 5;"),
    ("View: Revenue by Country", "SELECT * FROM v_revenue_by_country ORDER BY total_revenue DESC LIMIT 5;"),
    ("View: Top Performing Products", "SELECT * FROM v_top_performing_products LIMIT 5;"),
    ("Query 1: MoM Revenue Growth with LAG()", """
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
        ORDER BY year_month LIMIT 5;
    """),
    ("Query 2: 7-Day & 30-Day Rolling Averages", """
        SELECT 
            date_key,
            revenue,
            ROUND(AVG(revenue) OVER (ORDER BY date_key ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS rolling_7day,
            ROUND(AVG(revenue) OVER (ORDER BY date_key ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 2) AS rolling_30day
        FROM daily_sales
        ORDER BY date_key DESC LIMIT 5;
    """),
    ("Query 3: Top 3 Products Per Country with DENSE_RANK()", """
        WITH country_product_sales AS (
            SELECT 
                f.country,
                p.stock_code,
                p.description,
                ROUND(SUM(f.line_total), 2) AS product_revenue,
                DENSE_RANK() OVER (PARTITION BY f.country ORDER BY SUM(f.line_total) DESC) AS rank_within_country
            FROM fact_sales f
            JOIN dim_product p ON f.stock_code = p.stock_code
            WHERE f.country IN ('Germany', 'France')
            GROUP BY f.country, p.stock_code, p.description
        )
        SELECT * FROM country_product_sales WHERE rank_within_country <= 3;
    """),
    ("Query 5: Pareto 80/20 Cumulative Distribution", """
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
            ROUND((running_cumulative_rev / total_enterprise_rev) * 100, 2) AS cumulative_rev_pct
        FROM cumulative_calc
        ORDER BY item_rank LIMIT 5;
    """)
]

def validate():
    print("[*] Validating SQL Views & Queries against the database schema...")
    with engine.connect() as conn:
        for title, q in queries:
            print(f"\n--- Testing: {title} ---")
            df = pd.read_sql(text(q), conn)
            print(df.to_string(index=False))
            print(f"[+] Returned {len(df)} rows successfully.")
    print("\n[+] All SQL Views & Analytical Queries executed successfully with genuine data!")

if __name__ == "__main__":
    validate()
