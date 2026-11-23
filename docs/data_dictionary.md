# RetailIQ: Enterprise Data Dictionary

This document details all data entities, raw transactional fields, dimensional attributes, fact metrics, and business logic applied in the RetailIQ analytical data warehouse.

---

## 1. Source Dataset Specifications (UCI Online Retail)

| Field | Source Type | Description | Cleaning & Transformation Rule |
| :--- | :--- | :--- | :--- |
| `InvoiceNo` | String / Int | 6-digit integer assigned to each transaction. | Stripped of whitespace. Invoices prefixed with 'C' indicate cancellations. |
| `StockCode` | String | Unique product identifier code. | Standardized to uppercase. Non-product codes (`POST`, `D`, `CR`, `BANK CHARGES`) flagged. |
| `Description` | String | Nominal product name. | Missing descriptions filled with `'UNKNOWN ITEM'`. Whitespace trimmed. |
| `Quantity` | Integer | Volume of merchandise ordered. | Must be `> 0` for completed sales. Negative values segregated as cancellations or scrap. |
| `InvoiceDate` | String | Transaction timestamp (`m/d/yyyy h:mm`). | Parsed to standard ISO UTC timestamp. Derived calendar attributes created. |
| `UnitPrice` | Float | Price per item in Sterling (£). | Must be `> 0`. Zero or negative price adjustments filtered out. |
| `CustomerID` | Float | 5-digit customer identifier. | Non-null converted to integer string. Nulls preserved as unregistered Guest checkouts. |
| `Country` | String | Country of client residence. | Standardized strings. Missing values set to `'Unspecified'`. |

---

## 2. Dimensional Tables

### `dim_date` (Calendar Dimension)
Contains complete calendar attributes spanning every calendar day between min and max transaction dates.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `date_key` | DATE | Primary Key | Standard Gregorian calendar date (`YYYY-MM-DD`). |
| `year` | INTEGER | NOT NULL | 4-digit calendar year (e.g., `2011`). |
| `quarter` | INTEGER | NOT NULL | Calendar quarter (`1` to `4`). |
| `month` | INTEGER | NOT NULL | Calendar month number (`1` to `12`). |
| `month_name` | VARCHAR(20) | NOT NULL | Full month name (e.g., `'December'`). |
| `year_month` | VARCHAR(7) | NOT NULL, Indexed | Period identifier string (`'YYYY-MM'`). |
| `day_of_month` | INTEGER | NOT NULL | Day of month (`1` to `31`). |
| `day_of_week` | INTEGER | NOT NULL | ISO day of week (`0` = Monday, `6` = Sunday). |
| `day_name` | VARCHAR(20) | NOT NULL | Full name of day (e.g., `'Wednesday'`). |
| `is_weekend` | INTEGER | NOT NULL | `1` if Saturday or Sunday, else `0`. |
| `quarter_name` | VARCHAR(10) | NOT NULL | Year and quarter label (e.g., `'2011-Q4'`). |

---

### `dim_product` (Product Dimension)
Consolidates the active merchandise catalog, descriptions, and lifetime velocity statistics.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `stock_code` | VARCHAR(64) | Primary Key | Unique item identifier code. |
| `description` | TEXT | NOT NULL, Indexed | Canonical product description. |
| `avg_unit_price` | NUMERIC(12,2) | NOT NULL | Average realized selling price. |
| `total_lifetime_revenue`| NUMERIC(14,2) | NOT NULL | Cumulative lifetime sales revenue in GBP. |
| `total_lifetime_quantity`| BIGINT | NOT NULL | Cumulative lifetime units liquidated. |
| `first_sold_date` | TIMESTAMP | NULL | Earliest recorded sale timestamp. |
| `last_sold_date` | TIMESTAMP | NULL | Most recent recorded sale timestamp. |
| `is_active` | INTEGER | NOT NULL | `1` if active in catalog, `0` if archived. |

---

### `dim_customer` (Customer Dimension)
Consolidates registered commercial client profiles, geographic origin, and RFM scores.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `customer_id` | VARCHAR(64) | Primary Key | Identified client account code. |
| `country` | VARCHAR(100) | NOT NULL, Indexed | Primary territory of client registration. |
| `first_order_date` | TIMESTAMP | NULL | Account inception order date. |
| `last_order_date` | TIMESTAMP | NULL | Most recent transaction order date. |
| `total_orders` | INTEGER | NOT NULL | Cumulative count of distinct orders placed. |
| `total_spend` | NUMERIC(14,2) | NOT NULL | Cumulative historical spend across all orders. |
| `rfm_recency` | INTEGER | NULL | Elapsed days from last order to reference date. |
| `rfm_frequency` | INTEGER | NULL | Distinct order count. |
| `rfm_monetary` | NUMERIC(14,2) | NULL | Historical spend total. |
| `rfm_segment` | VARCHAR(50) | NULL, Indexed | Assigned RFM behavioral cohort (Champions, Loyal, At Risk, etc.). |

---

## 3. Fact Table

### `fact_sales` (Transaction Sales Fact)
Central transactional fact table recording completed merchandise line-item sales.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `sale_id` | BIGSERIAL | Primary Key | Surrogate primary key. |
| `invoice_no` | VARCHAR(64) | NOT NULL, Indexed | Commercial invoice number. |
| `stock_code` | VARCHAR(64) | Foreign Key (`dim_product`) | Foreign key linking to product catalog. |
| `customer_id` | VARCHAR(64) | Foreign Key (`dim_customer`) | Foreign key linking to customer (NULL for guests). |
| `date_key` | DATE | Foreign Key (`dim_date`) | Foreign key linking to calendar dimension. |
| `invoice_date` | TIMESTAMP | NOT NULL | Precise timestamp of purchase. |
| `quantity` | INTEGER | NOT NULL, CHECK > 0 | Units purchased in transaction line item. |
| `unit_price` | NUMERIC(12,4) | NOT NULL, CHECK > 0 | Unit selling price at time of purchase. |
| `line_total` | NUMERIC(14,2) | NOT NULL, CHECK >= 0| Gross line item revenue (`Quantity * UnitPrice`). |
| `country` | VARCHAR(100) | NOT NULL, Indexed | Destination country of shipment. |
| `is_guest` | INTEGER | NOT NULL | `1` for unregistered checkout, `0` for identified. |

---

## 4. Aggregate & Analytical Tables

### `daily_sales`
Pre-aggregated daily operational telemetry.
- `date_key` (DATE, PK): Day identifier.
- `revenue` (NUMERIC): Gross daily revenue.
- `order_count` (INTEGER): Distinct daily orders.
- `quantity_sold` (BIGINT): Total units liquidated.
- `unique_customers` (INTEGER): Distinct buyers active.
- `avg_order_value` (NUMERIC): `Revenue / Orders`.

### `monthly_sales`
Monthly financial performance and growth trends.
- `year_month` (VARCHAR(7), PK): Period (`YYYY-MM`).
- `revenue` (NUMERIC): Monthly total revenue.
- `order_count` (INTEGER): Monthly order count.
- `quantity_sold` (BIGINT): Monthly units sold.
- `unique_customers` (INTEGER): Distinct buyers.
- `mom_growth_pct` (NUMERIC): Month-over-month growth rate percentage.

### `inventory_parameters`
User-configurable and simulated replenishment decision attributes.
- `stock_code` (VARCHAR, PK): Product SKU.
- `current_stock` (INTEGER): On-hand inventory count.
- `lead_time_days` (INTEGER): Supplier replenishment lead time.
- `service_level_pct` (NUMERIC): Cycle service level target (e.g. 95.0%).
- `expected_lead_time_demand` (NUMERIC): Daily mean demand multiplied by lead time.
- `safety_stock` (INTEGER): Buffer stock: `Z * sqrt(LeadTime) * StdDev`.
- `reorder_point` (INTEGER): `LeadTimeDemand + SafetyStock`.
- `suggested_reorder_qty` (INTEGER): Order recommendation.
- `inventory_coverage_days` (NUMERIC): `CurrentStock / DailyDemand`.
- `stockout_risk_level` (VARCHAR): Risk classification (`Critical`, `High`, `Medium`, `Low`).

### `forecast_results`
Multi-horizon time-series machine learning outputs.
- `forecast_id` (BIGSERIAL, PK): Unique forecast identifier.
- `target_type` (VARCHAR): `'GLOBAL_REVENUE'` or `'PRODUCT_DEMAND'`.
- `target_identifier` (VARCHAR): `'ALL'` or StockCode.
- `model_name` (VARCHAR): Selected champion model name.
- `horizon_days` (INTEGER): Forecast horizon (`7`, `30`, or `90` days).
- `forecast_date` (DATE): Calendar date of forecast.
- `predicted_value` (NUMERIC): Point forecast value.
- `lower_bound` (NUMERIC): Lower 95% confidence interval bound.
- `upper_bound` (NUMERIC): Upper 95% confidence interval bound.
- `mae`, `rmse`, `mape`, `wape`: Out-of-time evaluation metrics.
