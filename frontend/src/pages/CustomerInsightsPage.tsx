import React, { useState, useEffect } from 'react';
import {
  Users,
  Award,
  AlertTriangle,
  Repeat,
  DollarSign,
  Search,
  Filter,
  Layers,
  ArrowRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { api } from '../services/api';
import { CustomerSummary, CustomerRFM } from '../types';
import { MetricCard } from '../components/MetricCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export const CustomerInsightsPage: React.FC = () => {
  const [summary, setSummary] = useState<CustomerSummary | null>(null);
  const [rfmList, setRfmList] = useState<CustomerRFM[]>([]);
  const [segmentFilter, setSegmentFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (seg?: string, search?: string) => {
    try {
      setLoading(true);
      const [sumData, rfmData] = await Promise.all([
        api.getCustomerSummary(),
        api.getCustomerRFM(50, seg, search),
      ]);
      setSummary(sumData);
      setRfmList(rfmData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load customer RFM analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFilterChange = (seg: string) => {
    setSegmentFilter(seg);
    loadData(seg, searchTerm);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData(segmentFilter, searchTerm);
  };

  if (loading) return <LoadingSpinner message="Calculating customer RFM quintiles..." />;
  if (error) return <ErrorAlert message={error} onRetry={() => loadData()} />;
  if (!summary) return null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
          Customer Insights & RFM Segmentation
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Behavioral customer segmentation based on Recency, Frequency, and Monetary quintile scores.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Identified Accounts"
          value={summary.total_identified_customers.toLocaleString()}
          subValue="Registered customer accounts"
          icon={Users}
        />
        <MetricCard
          title="Repeat Buyer Rate"
          value={`${summary.repeat_customer_rate_pct.toFixed(1)}%`}
          subValue={`${summary.repeat_customer_count.toLocaleString()} multi-order clients`}
          icon={Repeat}
          badge="High Retention"
          badgeType="success"
        />
        <MetricCard
          title="Avg Lifetime Spend"
          value={`£${summary.avg_customer_lifetime_spend.toFixed(2)}`}
          subValue="Historical customer revenue"
          icon={DollarSign}
        />
        <MetricCard
          title="Guest Ratio"
          value="24.9%"
          subValue="Unregistered checkout volume"
          icon={Layers}
        />
      </div>

      {/* Segment Distribution Chart & Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Comparison Chart */}
        <div className="lg:col-span-2 bg-surface border border-surface-border rounded-lg p-6">
          <h3 className="text-sm font-semibold text-white mb-1">
            Customer Share (%) vs. Revenue Share (%) by RFM Segment
          </h3>
          <p className="text-xs text-slate-400 mb-6">
            Illustrates commercial value concentration across customer cohorts.
          </p>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary.segments} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2e4f" vertical={false} />
                <XAxis dataKey="segment" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d1527', borderColor: '#1e2e4f', borderRadius: '6px' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                  formatter={(v: any) => [`${v}%`, 'Share']}
                />
                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                <Bar dataKey="customer_pct" name="Customer Population %" fill="#64748b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="spend_pct" name="Total Spend Contribution %" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Action Recommendations */}
        <div className="bg-surface border border-surface-border rounded-lg p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <Award className="w-4 h-4 text-cyan-400" />
              Strategic Retention Insights
            </h3>
            <p className="text-xs text-slate-400 mb-4">Targeted interventions for high-leverage segments.</p>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-surface-light rounded border border-surface-border">
                <span className="font-semibold text-cyan-400">Champions:</span>
                <p className="text-slate-300 mt-0.5">Reward with exclusive VIP early product access and premium loyalty rewards.</p>
              </div>
              <div className="p-3 bg-surface-light rounded border border-surface-border">
                <span className="font-semibold text-amber-400">At Risk:</span>
                <p className="text-slate-300 mt-0.5">High historical spenders going dormant. Dispatch personalized win-back discounts.</p>
              </div>
              <div className="p-3 bg-surface-light rounded border border-surface-border">
                <span className="font-semibold text-blue-400">Potential Loyalists:</span>
                <p className="text-slate-300 mt-0.5">High recent engagement. Introduce bundle discounts to expand order frequency.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Customer RFM Table */}
      <div className="bg-surface border border-surface-border rounded-lg p-6 space-y-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <Filter className="w-3.5 h-3.5 text-cyan-400" />
              <span>Segment Filter:</span>
            </div>
            <select
              value={segmentFilter}
              onChange={(e) => handleFilterChange(e.target.value)}
              className="bg-surface-light border border-surface-border text-xs text-slate-200 rounded px-3 py-1.5 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Cohorts</option>
              {summary.segments.map((s) => (
                <option key={s.segment} value={s.segment}>
                  {s.segment} ({s.customer_count})
                </option>
              ))}
            </select>
          </div>

          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full md:w-72">
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search Customer ID..."
                className="w-full bg-surface-light border border-surface-border text-xs text-slate-200 pl-8 pr-3 py-1.5 rounded focus:outline-none focus:border-cyan-500 placeholder-slate-500 font-mono"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium rounded transition-colors"
            >
              Filter
            </button>
          </form>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-surface-border text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Customer ID</th>
                <th className="py-3 px-4">Territory</th>
                <th className="py-3 px-4 text-right">Orders (F)</th>
                <th className="py-3 px-4 text-right">Recency (R)</th>
                <th className="py-3 px-4 text-right">Avg Order Value</th>
                <th className="py-3 px-4 text-right">Total Spend (M)</th>
                <th className="py-3 px-4 text-center">Assigned Segment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border font-mono">
              {rfmList.map((c) => (
                <tr key={c.customer_id} className="hover:bg-surface-light/40 transition-colors">
                  <td className="py-3 px-4 font-semibold text-cyan-400">#{c.customer_id}</td>
                  <td className="py-3 px-4 text-slate-200 font-sans">{c.country}</td>
                  <td className="py-3 px-4 text-right text-slate-300">{c.order_count}</td>
                  <td className="py-3 px-4 text-right text-slate-300">{c.recency_days} days ago</td>
                  <td className="py-3 px-4 text-right text-slate-300">£{c.avg_order_value.toFixed(2)}</td>
                  <td className="py-3 px-4 text-right font-bold text-white">
                    £{c.total_spend.toLocaleString('en-GB', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4 text-center font-sans">
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full border bg-surface-light text-cyan-300 border-cyan-500/30">
                      {c.segment}
                    </span>
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
