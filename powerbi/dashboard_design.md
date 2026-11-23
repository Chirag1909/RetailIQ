# RetailIQ: Power BI Executive Dashboard Specification

This specification outlines the visual layout, user experience hierarchy, slicer architecture, and visual components for implementing the 5 core RetailIQ enterprise report pages in Power BI Desktop / Power BI Service.

---

## Brand Theme & Color Palette

- **Background Canvas:** `#090D16` (Deep Dark Navy)
- **Visual Surface Containers:** `#0D1527` (Charcoal Blue)
- **Container Borders:** `#1E2E4F` (Subtle Navy Slate)
- **Data Series 1 (Primary Cyan):** `#06B6D4`
- **Data Series 2 (Secondary Sky):** `#38BDF8`
- **Data Series 3 (Accent Blue):** `#2563EB`
- **Success / Positive Growth:** `#10B981` (Emerald)
- **Warning / Moderate Risk:** `#F59E0B` (Amber)
- **Critical / Stockout Risk:** `#F43F5E` (Rose)
- **Text Headers:** `#FFFFFF`
- **Text Body / Muted:** `#94A3B8`

---

## Page 1: Executive Overview Dashboard

### Purpose
Executive summary displaying top-line financial health, order throughput, customer retention, and macro seasonality.

### Visual Architecture (Top to Bottom)
1. **Header Banner:**
   - RetailIQ Enterprise Analytics title
   - Live Dataset indicator (UCI Online Retail)
   - Slicers: Date Range (`dim_date[date_key]`), Country Dropdown (`dim_customer[country]`).
2. **Top KPI Ribbon (6 Multi-Row Cards):**
   - Total Cleaned Revenue (`£10.27M`)
   - Completed Orders (`19,792`)
   - Merchandise Units Liquidated (`5.17M`)
   - Average Order Value (`£518.70`)
   - Unique Customer Accounts (`4,334`)
   - Repeat Customer Ratio (`65.6%`)
3. **Primary Analytics Grid (2/3 Split):**
   - **Left Visual (Width 65%):** Line & Clustered Column Chart:
     - X-Axis: `dim_date[year_month]`
     - Column Y-Axis: `[Total Revenue]` (Cyan `#0284c7`)
     - Line Y-Axis: `[Month-over-Month (MoM) Growth %]` (Sky Blue `#38bdf8`)
     - Tooltip: Total Orders, Units Sold.
   - **Right Visual (Width 35%):** Clustered Bar Chart:
     - Y-Axis: `dim_customer[country]` (Top 8 countries)
     - X-Axis: `[Total Revenue]`
     - Data Labels: On (Inside End, £M format).
4. **Bottom Grid:**
   - Top 10 High-Revenue SKUs (Table Visual with conditional revenue heatmaps).

---

## Page 2: Sales Performance & Transaction Ledger

### Purpose
Operational deep-dive into sales channels, order size distribution, and transaction audit trails.

### Visual Architecture
1. **Slicers:** Date Range, Country, Invoice Search, Price Band.
2. **Time-Series Area Chart:**
   - X-Axis: `dim_date[date_key]` (Daily frequency)
   - Values: `[Total Revenue]` and `[7-Day Moving Average Revenue]`.
3. **Order Size Distribution:**
   - Histogram / Column chart binning orders into spend buckets: `£0-£100`, `£100-£500`, `£500-£2000`, `£2000+`.
4. **Detailed Transaction Fact Ledger (Table Visual):**
   - Columns: `InvoiceNo`, `InvoiceDate`, `StockCode`, `Description`, `Quantity`, `UnitPrice`, `LineTotal`, `Country`, `CustomerID`.

---

## Page 3: Product Intelligence & Demand Velocity

### Purpose
Merchandise velocity analysis, Pareto 80/20 verification, and catalog turnover.

### Visual Architecture
1. **Slicers:** Velocity Tier (`High Velocity`, `Medium Velocity`, `Low Velocity`), Product Search.
2. **Top Metrics Cards:**
   - Monitored SKUs (`3,805`)
   - Pareto Concentration (`79.4%` from Top 20% SKUs)
   - High-Velocity SKU Count (`381`)
3. **Pareto Cumulative Curve (Line Chart):**
   - X-Axis: SKU Rank (1 to 3,805)
   - Y-Axis: `[Pareto Cumulative Share %]` with constant 80% benchmark reference line.
4. **Product Velocity Matrix:**
   - Scatter Plot: X-Axis = Order Frequency, Y-Axis = Total Revenue, Size = Units Sold.

---

## Page 4: Customer Segmentation & RFM Behavior

### Purpose
Cohort intelligence separating high-value champions from at-risk accounts.

### Visual Architecture
1. **Slicers:** RFM Segment (`Champions`, `Loyal Customers`, `Potential Loyalists`, `At Risk`, `Hibernating`), Country.
2. **RFM Segment Breakdown Visuals:**
   - Clustered Bar Chart: Customer Population % vs Spend Contribution % by Segment.
   - Treemap: Sized by `[Total Revenue]`, color-coded by `dim_customer[rfm_segment]`.
3. **Strategic Cohort Table:**
   - Columns: `Segment`, `Customer Count`, `Total Spend`, `Spend %`, `Avg Recency (Days)`, `Avg Frequency`, `Recommended Business Action`.
4. **Account Search Explorer:**
   - Detailed customer table with `CustomerID`, `Country`, `FirstOrderDate`, `LastOrderDate`, `Orders`, `TotalSpend`, `Recency`.

---

## Page 5: Demand Forecasting & Inventory Optimization

### Purpose
Machine learning forecast outputs linked to scientific replenishment recommendations.

### Visual Architecture
1. **Slicers:** Horizon Selector (`7 Days`, `30 Days`, `90 Days`), Target Selector (`Global Revenue` vs Top Products).
2. **Actual vs. Forecast Trajectory (Line Chart):**
   - Historical Actuals (`#94A3B8`)
   - Predicted Value (`#06B6D4`)
   - Confidence Bounds 95% (Upper & Lower dotted lines).
3. **Model Leaderboard Table:**
   - Architecture Comparison: Seasonal Naive, Holt-Winters, XGBoost Regressor.
   - Metrics: MAE, RMSE, MAPE, WAPE.
4. **Replenishment Action Table:**
   - Columns: `StockCode`, `Description`, `CurrentStock`, `SafetyStock`, `ReorderPoint`, `SuggestedReorderQty`, `CoverageDays`, `StockoutRiskLevel`.
   - Conditional formatting: Red highlight for `Critical` and Amber for `High`.
