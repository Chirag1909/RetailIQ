# RetailIQ: Power BI DAX Measures & Modeling Dictionary

This document specifies the standard DAX (Data Analysis Expressions) measures, dimensional relationship schema, and PostgreSQL connection protocols for building enterprise Power BI reports on the RetailIQ data warehouse.

---

## 1. Database Connection Protocol

### PostgreSQL DirectQuery & Import Modes
- **Server:** `localhost:5432` (or cloud host)
- **Database:** `retailiq_db`
- **Data Connectivity Mode:** `Import` (Recommended for high-performance in-memory caching and DAX time-intelligence functions) or `DirectQuery` for real-time transactional monitoring.
- **Credential Storage:** Windows Authentication or Database Service Account (never embed credentials in `.pbix`).

### Primary Tables & Analytical Views to Import
1. `fact_sales` (Transaction Fact)
2. `dim_date` (Calendar Dimension)
3. `dim_product` (Product Dimension)
4. `dim_customer` (Customer Dimension)
5. `daily_sales` (Pre-aggregated Daily Performance)
6. `monthly_sales` (Pre-aggregated Monthly Performance)
7. `v_revenue_by_month` (Analytical View)
8. `v_top_performing_products` (Analytical View)
9. `v_product_demand_trends` (Analytical View)

---

## 2. Dimensional Data Model & Relationships

```
dim_date [date_key] 1 ----< * fact_sales [date_key] (Single Direction, Active)
dim_product [stock_code] 1 ----< * fact_sales [stock_code] (Single Direction, Active)
dim_customer [customer_id] 1 ----< * fact_sales [customer_id] (Single Direction, Both)
```

---

## 3. Core DAX Measure Library

### 1. Revenue & Sales Volume

```dax
Total Revenue = 
SUM(fact_sales[line_total])
```

```dax
Total Orders = 
DISTINCTCOUNT(fact_sales[invoice_no])
```

```dax
Total Units Sold = 
SUM(fact_sales[quantity])
```

```dax
Average Order Value (AOV) = 
DIVIDE([Total Revenue], [Total Orders], 0)
```

```dax
Average Item Price = 
AVERAGE(fact_sales[unit_price])
```

---

### 2. Time Intelligence & Growth Measures

```dax
Previous Month Revenue = 
CALCULATE(
    [Total Revenue],
    DATEADD(dim_date[date_key], -1, MONTH)
)
```

```dax
Month-over-Month (MoM) Growth % = 
VAR PrevMonth = [Previous Month Revenue]
RETURN
    IF(
        NOT ISBLANK(PrevMonth),
        DIVIDE([Total Revenue] - PrevMonth, PrevMonth, 0) * 100,
        BLANK()
    )
```

```dax
7-Day Moving Average Revenue = 
AVERAGEX(
    DATESINPERIOD(
        dim_date[date_key],
        LASTDATE(dim_date[date_key]),
        -7,
        DAY
    ),
    [Total Revenue]
)
```

```dax
30-Day Moving Average Revenue = 
AVERAGEX(
    DATESINPERIOD(
        dim_date[date_key],
        LASTDATE(dim_date[date_key]),
        -30,
        DAY
    ),
    [Total Revenue]
)
```

```dax
Year-to-Date (YTD) Revenue = 
TOTALYTD([Total Revenue], dim_date[date_key])
```

---

### 3. Customer Analytics & Retention

```dax
Unique Active Customers = 
DISTINCTCOUNT(fact_sales[customer_id])
```

```dax
Repeat Customers = 
CALCULATE(
    DISTINCTCOUNT(fact_sales[customer_id]),
    FILTER(
        VALUES(fact_sales[customer_id]),
        CALCULATE(DISTINCTCOUNT(fact_sales[invoice_no])) > 1
    )
)
```

```dax
Repeat Customer Rate % = 
DIVIDE([Repeat Customers], [Unique Active Customers], 0) * 100
```

```dax
Average Customer Lifetime Revenue = 
DIVIDE([Total Revenue], [Unique Active Customers], 0)
```

---

### 4. Cumulative Distribution & Pareto 80/20

```dax
Running Cumulative Product Revenue = 
VAR CurrentProductRevenue = [Total Revenue]
RETURN
    CALCULATE(
        [Total Revenue],
        FILTER(
            ALLSELECTED(dim_product[stock_code]),
            [Total Revenue] >= CurrentProductRevenue
        )
    )
```

```dax
Pareto Cumulative Share % = 
VAR TotalEnterpriseRevenue = CALCULATE([Total Revenue], ALLSELECTED(fact_sales))
RETURN
    DIVIDE([Running Cumulative Product Revenue], TotalEnterpriseRevenue, 0) * 100
```

```dax
Top 20% Product Revenue Share % = 
CALCULATE(
    [Total Revenue],
    TOPN(
        ROUNDUP(COUNTROWS(ALL(dim_product)) * 0.2, 0),
        ALL(dim_product),
        [Total Revenue],
        DESC
    )
) / CALCULATE([Total Revenue], ALL(dim_product)) * 100
```

---

### 5. Inventory Replenishment Indicators

```dax
Stockout Risk Flag = 
SWITCH(
    TRUE(),
    SELECTEDVALUE(inventory_parameters[stockout_risk_level]) = "Critical", "🔴 Critical",
    SELECTEDVALUE(inventory_parameters[stockout_risk_level]) = "High", "🟠 High",
    SELECTEDVALUE(inventory_parameters[stockout_risk_level]) = "Medium", "🟡 Medium",
    "🟢 Low"
)
```
