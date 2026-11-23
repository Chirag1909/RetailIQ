import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  ShoppingCart,
  Layers,
  CreditCard,
  Users,
  Repeat,
  ArrowUpRight,
  ArrowDownRight,
  Globe,
  TrendingUp,
  FileSpreadsheet,
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  BarChart,
} from 'recharts';
import { api } from '../services/api';
import {
  DashboardSummary,
  MonthlySaleItem,
  TopProductItem,
  CountryPerformanceItem,
} from '../types';
import { MetricCard } from '../components/MetricCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export const OverviewPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [monthlySales, setMonthlySales] = useState<MonthlySaleItem[]>([]);
  const [topProducts, setTopProducts] = useState<TopProductItem[]>([]);
  const [countries, setCountries] = useState<CountryPerformanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumData, monthlyData, prodData, countryData] = await Promise.all([
        api.getDashboardSummary(),
        api.getMonthlySales(),
        api.getTopProducts(10),
        api.getCountryPerformance(8),
      ]);
      setSummary(sumData);
      setMonthlySales(monthlyData);
      setTopProducts(prodData);
      setCountries(countryData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load executive summary data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    window.addEventListener('retailiq:refresh', loadData);
    return () => window.removeEventListener('retailiq:refresh', loadData);
  }, []);

  if (loading) return <LoadingSpinner message="Calculating real platform metrics..." />;
  if (error) return <ErrorAlert message={error} onRetry={loadData} />;
  if (!summary) return null;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
          Executive Overview
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          High-level enterprise performance metrics transformed from UCI retail transactions.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Cleaned Revenue"
          value={`£${summary.total_revenue.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`}
          subValue="522,710 valid sales"
          icon={DollarSign}
          badge="Verified"
          badgeType="success"
        />
        <MetricCard
          title="Completed Orders"
          value={summary.total_orders.toLocaleString()}
          subValue="Distinct invoices"
          icon={ShoppingCart}
        />
        <MetricCard
          title="Units Liquidated"
          value={summary.units_sold.toLocaleString()}
          subValue="Total merchandise items"
          icon={Layers}
        />
        <MetricCard
          title="Average Order Value"
          value={`£${summary.average_order_value.toFixed(2)}`}
          subValue="Gross revenue / orders"
          icon={CreditCard}
        />
        <MetricCard
          title="Unique Customers"
          value={summary.unique_customers.toLocaleString()}
          subValue="Identified accounts"
          icon={Users}
        />
        <MetricCard
          title="Repeat Customer Rate"
          value={`${summary.repeat_customer_rate.toFixed(1)}%`}
          subValue="Multi-order accounts"
          icon={Repeat}
          badge={summary.repeat_customer_rate > 60 ? 'Strong' : 'Moderate'}
          badgeType={summary.repeat_customer_rate > 60 ? 'success' : 'warning'}
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Revenue & Growth (2 Columns) */}
        <div className="lg:col-span-2 bg-surface border border-surface-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                Monthly Revenue & MoM Growth Trajectory
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Demonstrates seasonality surge in Q4 ahead of holiday procurement.
              </p>
            </div>
          </div>

          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={monthlySales} margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2e4f" vertical={false} />
                <XAxis dataKey="year_month" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis
                  yAxisId="left"
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => `£${(v / 1000).toFixed(0)}k`}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke="#38bdf8"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d1527', borderColor: '#1e2e4f', borderRadius: '6px' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                  formatter={(val: any, name: string) => [
                    name === 'Revenue (£)' ? `£${Number(val).toLocaleString()}` : `${val}%`,
                    name,
                  ]}
                />
                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                <Bar yAxisId="left" dataKey="revenue" name="Revenue (£)" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="mom_growth_pct"
                  name="MoM Growth (%)"
                  stroke="#38bdf8"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#38bdf8' }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Global Geographic Distribution (1 Column) */}
        <div className="bg-surface border border-surface-border rounded-lg p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
              <Globe className="w-4 h-4 text-cyan-400" />
              Top Global Markets
            </h3>
            <p className="text-xs text-slate-400 mb-4">Revenue contribution by key export territories.</p>

            <div className="space-y-3">
              {countries.map((c) => (
                <div key={c.country} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-200">{c.country}</span>
                    <span className="text-slate-400 font-mono">
                      £{c.total_revenue.toLocaleString()} ({c.global_share_pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-surface-lighter h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-cyan-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, c.global_share_pct)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-surface-border text-xs text-slate-400 flex items-center justify-between">
            <span>Domestic dominance:</span>
            <span className="font-semibold text-cyan-300 font-mono">UK ~85.1% Total</span>
          </div>
        </div>
      </div>

      {/* Top Products Table */}
      <div className="bg-surface border border-surface-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
              Top 10 High-Revenue Merchandise SKUs
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Ranked by aggregate historical turnover across the 12-month period.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-surface-border text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Rank</th>
                <th className="py-3 px-4">SKU Code</th>
                <th className="py-3 px-4">Description</th>
                <th className="py-3 px-4 text-right">Units Sold</th>
                <th className="py-3 px-4 text-right">Total Revenue (£)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border font-mono">
              {topProducts.map((p, idx) => (
                <tr key={p.stock_code} className="hover:bg-surface-light/40 transition-colors">
                  <td className="py-3 px-4 text-slate-400 font-semibold">#{idx + 1}</td>
                  <td className="py-3 px-4 text-cyan-400 font-medium">{p.stock_code}</td>
                  <td className="py-3 px-4 text-slate-200 font-sans">{p.description}</td>
                  <td className="py-3 px-4 text-right text-slate-300">{p.total_quantity.toLocaleString()}</td>
                  <td className="py-3 px-4 text-right font-bold text-white">
                    £{p.total_revenue.toLocaleString('en-GB', { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
