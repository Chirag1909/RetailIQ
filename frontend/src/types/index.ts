// RetailIQ TypeScript Type Definitions

export interface HealthStatus {
  status: string;
  database_connected: boolean;
  timestamp: string;
  environment: string;
}

export interface PlatformMetadata {
  project_name: string;
  version: string;
  description: string;
  dataset_source: string;
  supported_models: string[];
  forecast_horizons: number[];
}

export interface DashboardSummary {
  total_revenue: number;
  total_orders: number;
  units_sold: number;
  average_order_value: number;
  unique_customers: number;
  repeat_customer_rate: number;
  active_products: number;
  monitored_countries: number;
  quality_score: number;
}

export interface RevenueTrendItem {
  date: string;
  revenue: number;
  orders: number;
  quantity: number;
}

export interface TopProductItem {
  stock_code: string;
  description: string;
  total_revenue: number;
  total_quantity: number;
  revenue_rank?: number;
}

export interface CountryPerformanceItem {
  country: string;
  total_revenue: number;
  total_orders: number;
  total_customers: number;
  avg_order_value: number;
  global_share_pct: number;
}

export interface SaleRecord {
  sale_id: number;
  invoice_no: string;
  stock_code: string;
  customer_id: string | null;
  invoice_date: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  country: string;
  is_guest: number;
}

export interface SalesPaginatedResponse {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  data: SaleRecord[];
}

export interface MonthlySaleItem {
  year_month: string;
  revenue: number;
  orders: number;
  quantity: number;
  unique_customers: number;
  mom_growth_pct: number;
}

export interface ProductSummary {
  stock_code: string;
  description: string;
  total_revenue: number;
  total_quantity: number;
  order_count: number;
  avg_unit_price: number;
  revenue_rank?: number;
  demand_velocity_category?: string;
}

export interface CustomerSegment {
  segment: string;
  customer_count: number;
  customer_pct: number;
  total_spend: number;
  spend_pct: number;
  avg_recency_days: number;
  avg_frequency: number;
  avg_monetary: number;
  description: string;
}

export interface CustomerSummary {
  total_identified_customers: number;
  total_historical_spend: number;
  avg_customer_lifetime_spend: number;
  repeat_customer_count: number;
  repeat_customer_rate_pct: number;
  segments: CustomerSegment[];
}

export interface CustomerRFM {
  customer_id: string;
  country: string;
  total_spend: number;
  order_count: number;
  recency_days: number;
  avg_order_value: number;
  segment?: string;
}

export interface ForecastPoint {
  forecast_date: string;
  predicted_value: number;
  lower_bound: number | null;
  upper_bound: number | null;
}

export interface ForecastResponse {
  target_type: string;
  target_identifier: string;
  horizon_days: number;
  model_name: string;
  mae: number | null;
  rmse: number | null;
  mape: number | null;
  wape: number | null;
  trained_at: string;
  forecasts: ForecastPoint[];
  historical_baseline?: Array<{ date: string; actual: number }>;
}

export interface ForecastModelAccuracy {
  model_name: string;
  mae: number;
  rmse: number;
  mape: number;
  wape: number;
  is_champion: boolean;
}

export interface ForecastAccuracyResponse {
  target_identifier: string;
  leaderboard: ForecastModelAccuracy[];
}

export interface InventoryItem {
  stock_code: string;
  description: string;
  current_stock: number;
  lead_time_days: number;
  service_level_pct: number;
  expected_lead_time_demand: number;
  safety_stock: number;
  reorder_point: number;
  suggested_reorder_qty: number;
  inventory_coverage_days: number;
  stockout_risk_level: string; // Critical, High, Medium, Low
  overstock_risk_level: string;
  action_recommendation?: string;
}

export interface InventoryOverview {
  total_monitored_skus: number;
  critical_stockout_count: number;
  high_stockout_count: number;
  overstock_risk_count: number;
  average_coverage_days: number;
  inventory_items: InventoryItem[];
}

export interface PipelineRunItem {
  run_id: string;
  pipeline_name: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  records_extracted: number;
  records_cleaned: number;
  records_loaded: number;
  data_quality_score: number | null;
  execution_duration_sec: number | null;
  error_message: string | null;
  triggered_by: string;
}

export interface PipelineStatus {
  latest_run: PipelineRunItem | null;
  total_runs: number;
  system_health: string;
  last_quality_score: number;
}

export interface DataQualityReport {
  report_id: string;
  generated_at: string;
  overall_quality_score: number;
  status: string;
  scoring_breakdown: {
    completeness_score: number;
    validity_score: number;
    uniqueness_score: number;
    formula: string;
  };
  summary_metrics: {
    raw_records: number;
    cleaned_records: number;
    retention_rate_pct: number;
    total_valid_revenue: number;
    unique_products: number;
    unique_customers: number;
    unique_countries: number;
  };
  anomalies_detected: {
    duplicate_rows: number;
    missing_customer_ids: number;
    missing_descriptions: number;
    cancellations_flagged: number;
    invalid_or_zero_unit_prices: number;
    negative_quantities: number;
    quantity_outliers_gt_5000: number;
    unit_price_outliers_gt_500: number;
  };
  temporal_coverage: {
    min_date: string;
    max_date: string;
    total_days_active: number;
  };
}
