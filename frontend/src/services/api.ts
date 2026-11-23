import axios from 'axios';
import {
  HealthStatus,
  PlatformMetadata,
  DashboardSummary,
  RevenueTrendItem,
  TopProductItem,
  CountryPerformanceItem,
  SalesPaginatedResponse,
  MonthlySaleItem,
  ProductSummary,
  CustomerSummary,
  CustomerSegment,
  CustomerRFM,
  ForecastResponse,
  ForecastAccuracyResponse,
  InventoryOverview,
  InventoryItem,
  PipelineStatus,
  PipelineRunItem,
  DataQualityReport,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health & Metadata
  getHealth: async (): Promise<HealthStatus> => {
    const res = await apiClient.get<HealthStatus>('/health');
    return res.data;
  },
  getMetadata: async (): Promise<PlatformMetadata> => {
    const res = await apiClient.get<PlatformMetadata>('/metadata');
    return res.data;
  },

  // Dashboard
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const res = await apiClient.get<DashboardSummary>('/dashboard/summary');
    return res.data;
  },
  getRevenueTrend: async (startDate?: string, endDate?: string): Promise<RevenueTrendItem[]> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const res = await apiClient.get<RevenueTrendItem[]>(`/dashboard/revenue-trend?${params.toString()}`);
    return res.data;
  },
  getTopProducts: async (limit: number = 10): Promise<TopProductItem[]> => {
    const res = await apiClient.get<TopProductItem[]>(`/dashboard/top-products?limit=${limit}`);
    return res.data;
  },
  getCountryPerformance: async (limit: number = 10): Promise<CountryPerformanceItem[]> => {
    const res = await apiClient.get<CountryPerformanceItem[]>(`/dashboard/country-performance?limit=${limit}`);
    return res.data;
  },

  // Sales Analytics
  getSalesTransactions: async (
    page: number = 1,
    pageSize: number = 50,
    country?: string,
    stockCode?: string,
    search?: string
  ): Promise<SalesPaginatedResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (country && country !== 'ALL') params.append('country', country);
    if (stockCode) params.append('stock_code', stockCode);
    if (search) params.append('search', search);

    const res = await apiClient.get<SalesPaginatedResponse>(`/sales?${params.toString()}`);
    return res.data;
  },
  getMonthlySales: async (): Promise<MonthlySaleItem[]> => {
    const res = await apiClient.get<MonthlySaleItem[]>('/sales/monthly');
    return res.data;
  },
  getProductMetrics: async (limit: number = 50, search?: string, velocity?: string): Promise<ProductSummary[]> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (search) params.append('search', search);
    if (velocity && velocity !== 'ALL') params.append('velocity', velocity);
    const res = await apiClient.get<ProductSummary[]>(`/sales/products?${params.toString()}`);
    return res.data;
  },

  // Customers & RFM
  getCustomerSummary: async (): Promise<CustomerSummary> => {
    const res = await apiClient.get<CustomerSummary>('/customers/summary');
    return res.data;
  },
  getCustomerSegments: async (): Promise<CustomerSegment[]> => {
    const res = await apiClient.get<CustomerSegment[]>('/customers/segments');
    return res.data;
  },
  getCustomerRFM: async (limit: number = 50, segment?: string, search?: string): Promise<CustomerRFM[]> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (segment && segment !== 'ALL') params.append('segment', segment);
    if (search) params.append('search', search);
    const res = await apiClient.get<CustomerRFM[]>(`/customers/rfm?${params.toString()}`);
    return res.data;
  },

  // Demand Forecasting
  getForecast: async (
    targetType: string = 'GLOBAL_REVENUE',
    targetIdentifier: string = 'ALL',
    horizonDays: number = 30
  ): Promise<ForecastResponse> => {
    const res = await apiClient.get<ForecastResponse>(
      `/forecast?target_type=${targetType}&target_identifier=${targetIdentifier}&horizon_days=${horizonDays}`
    );
    return res.data;
  },
  getForecastAccuracy: async (targetIdentifier: string = 'ALL'): Promise<ForecastAccuracyResponse> => {
    const res = await apiClient.get<ForecastAccuracyResponse>(`/forecast/accuracy?target_identifier=${targetIdentifier}`);
    return res.data;
  },
  getAvailableModels: async (): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/forecast/models');
    return res.data;
  },

  // Inventory Optimization
  getInventoryOverview: async (riskLevel?: string, search?: string, limit: number = 50): Promise<InventoryOverview> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (riskLevel && riskLevel !== 'ALL') params.append('risk_level', riskLevel);
    if (search) params.append('search', search);
    const res = await apiClient.get<InventoryOverview>(`/inventory/overview?${params.toString()}`);
    return res.data;
  },
  getInventoryRecommendations: async (limit: number = 25): Promise<InventoryItem[]> => {
    const res = await apiClient.get<InventoryItem[]>(`/inventory/recommendations?limit=${limit}`);
    return res.data;
  },
  updateInventoryParameters: async (
    productId: string,
    params: {
      current_stock?: number;
      lead_time_days?: number;
      service_level_pct?: number;
      holding_cost?: number;
      reorder_cost?: number;
    }
  ): Promise<InventoryItem> => {
    const res = await apiClient.put<InventoryItem>(`/inventory/parameters/${productId}`, params);
    return res.data;
  },

  // Pipeline Orchestration
  getPipelineStatus: async (): Promise<PipelineStatus> => {
    const res = await apiClient.get<PipelineStatus>('/pipeline/status');
    return res.data;
  },
  getPipelineHistory: async (): Promise<PipelineRunItem[]> => {
    const res = await apiClient.get<PipelineRunItem[]>('/pipeline/history');
    return res.data;
  },
  triggerPipelineRun: async (): Promise<{ status: string; message: string }> => {
    const res = await apiClient.post<{ status: string; message: string }>('/pipeline/run');
    return res.data;
  },

  // Data Quality & Upload
  getDataQualityReport: async (): Promise<DataQualityReport> => {
    const res = await apiClient.get<DataQualityReport>('/data/quality-report');
    return res.data;
  },
  uploadDataset: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/data/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};
