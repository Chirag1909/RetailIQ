import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  Download,
  Calendar,
  Layers,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { api } from '../services/api';
import { SaleRecord, SalesPaginatedResponse, RevenueTrendItem } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export const SalesPage: React.FC = () => {
  const [trendData, setTrendData] = useState<RevenueTrendItem[]>([]);
  const [salesResponse, setSalesResponse] = useState<SalesPaginatedResponse | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [countryFilter, setCountryFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load initial trend and sales
  useEffect(() => {
    const fetchInitial = async () => {
      try {
        setLoading(true);
        const [trend, sales] = await Promise.all([
          api.getRevenueTrend(),
          api.getSalesTransactions(1, pageSize),
        ]);
        setTrendData(trend);
        setSalesResponse(sales);
      } catch (err: any) {
        setError(err?.message || 'Failed to load sales analytics.');
      } finally {
        setLoading(false);
      }
    };
    fetchInitial();
  }, []);

  // Fetch page or filter changes
  const fetchPage = async (newPage: number, country: string, search: string) => {
    try {
      setTableLoading(true);
      const res = await api.getSalesTransactions(newPage, pageSize, country, undefined, search || undefined);
      setSalesResponse(res);
      setPage(newPage);
    } catch (err: any) {
      setError(err?.message || 'Failed to update transaction table.');
    } finally {
      setTableLoading(false);
    }
  };

  const handleCountryChange = (c: string) => {
    setCountryFilter(c);
    fetchPage(1, c, searchTerm);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPage(1, countryFilter, searchTerm);
  };

  const exportCurrentTableToCSV = () => {
    if (!salesResponse || salesResponse.data.length === 0) return;
    const headers = ['Sale ID', 'Invoice No', 'Stock Code', 'Invoice Date', 'Quantity', 'Unit Price', 'Line Total', 'Country', 'Customer ID'];
    const rows = salesResponse.data.map(s => [
      s.sale_id, s.invoice_no, s.stock_code, s.invoice_date, s.quantity, s.unit_price, s.line_total, s.country, s.customer_id || 'Guest'
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `retailiq_sales_page_${page}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) return <LoadingSpinner message="Querying transaction records..." />;
  if (error) return <ErrorAlert message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
            Sales Analytics & Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Daily demand trajectory, volumetric distribution, and transactional fact explorer.
          </p>
        </div>
        <button
          onClick={exportCurrentTableToCSV}
          className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-medium bg-surface-light hover:bg-surface-lighter text-cyan-400 border border-cyan-500/30 rounded-md transition-colors"
        >
          <Download className="w-3.5 h-3.5" /> Export Page CSV
        </button>
      </div>

      {/* Daily Revenue Time-Series Chart */}
      <div className="bg-surface border border-surface-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              Daily Revenue Trajectory (Full Historical Horizon)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">374 continuous calendar days of retail activity.</p>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
              <defs>
                <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2e4f" vertical={false} />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => `£${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#0d1527', borderColor: '#1e2e4f', borderRadius: '6px' }}
                labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                formatter={(val: any) => [`£${Number(val).toLocaleString()}`, 'Daily Revenue']}
              />
              <Area type="monotone" dataKey="revenue" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#revenueFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Granular Transactions Table Section */}
      <div className="bg-surface border border-surface-border rounded-lg p-6 space-y-4">
        {/* Filters and Search Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <Filter className="w-3.5 h-3.5 text-cyan-400" />
              <span>Country:</span>
            </div>
            <select
              value={countryFilter}
              onChange={(e) => handleCountryChange(e.target.value)}
              className="bg-surface-light border border-surface-border text-xs text-slate-200 rounded px-3 py-1.5 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Territories (Global)</option>
              <option value="United Kingdom">United Kingdom</option>
              <option value="Germany">Germany</option>
              <option value="France">France</option>
              <option value="EIRE">EIRE (Ireland)</option>
              <option value="Netherlands">Netherlands</option>
              <option value="Spain">Spain</option>
              <option value="Australia">Australia</option>
            </select>
          </div>

          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full md:w-72">
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search Invoice or SKU..."
                className="w-full bg-surface-light border border-surface-border text-xs text-slate-200 pl-8 pr-3 py-1.5 rounded focus:outline-none focus:border-cyan-500 placeholder-slate-500 font-mono"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium rounded transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        {/* Table */}
        <div className="overflow-x-auto relative">
          {tableLoading && (
            <div className="absolute inset-0 bg-surface/70 backdrop-blur-sm flex items-center justify-center z-10">
              <div className="text-xs text-cyan-400 font-mono">Loading records...</div>
            </div>
          )}

          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-surface-border text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Invoice No</th>
                <th className="py-3 px-4">SKU</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Quantity</th>
                <th className="py-3 px-4 text-right">Unit Price (£)</th>
                <th className="py-3 px-4 text-right">Line Total (£)</th>
                <th className="py-3 px-4">Territory</th>
                <th className="py-3 px-4">Customer</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border font-mono">
              {salesResponse?.data.map((sale) => (
                <tr key={sale.sale_id} className="hover:bg-surface-light/40 transition-colors">
                  <td className="py-2.5 px-4 font-semibold text-cyan-400">{sale.invoice_no}</td>
                  <td className="py-2.5 px-4 text-slate-200">{sale.stock_code}</td>
                  <td className="py-2.5 px-4 text-slate-400 font-sans">{sale.invoice_date.slice(0, 16)}</td>
                  <td className="py-2.5 px-4 text-right text-slate-300">{sale.quantity}</td>
                  <td className="py-2.5 px-4 text-right text-slate-300">£{sale.unit_price.toFixed(2)}</td>
                  <td className="py-2.5 px-4 text-right font-bold text-white">£{sale.line_total.toFixed(2)}</td>
                  <td className="py-2.5 px-4 font-sans text-slate-300">{sale.country}</td>
                  <td className="py-2.5 px-4">
                    {sale.customer_id ? (
                      <span className="text-slate-300">#{sale.customer_id}</span>
                    ) : (
                      <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">Guest</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {salesResponse && (
          <div className="flex items-center justify-between pt-4 border-t border-surface-border text-xs text-slate-400">
            <div>
              Showing <span className="text-slate-200 font-mono">{(page - 1) * pageSize + 1}</span> to{' '}
              <span className="text-slate-200 font-mono">{Math.min(page * pageSize, salesResponse.total_count)}</span> of{' '}
              <span className="text-slate-200 font-mono">{salesResponse.total_count.toLocaleString()}</span> entries
            </div>

            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1 || tableLoading}
                onClick={() => fetchPage(page - 1, countryFilter, searchTerm)}
                className="p-1.5 rounded bg-surface-light hover:bg-surface-lighter text-slate-300 disabled:opacity-40 border border-surface-border transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2 font-mono text-slate-200">
                Page {page} of {salesResponse.total_pages}
              </span>
              <button
                disabled={page >= salesResponse.total_pages || tableLoading}
                onClick={() => fetchPage(page + 1, countryFilter, searchTerm)}
                className="p-1.5 rounded bg-surface-light hover:bg-surface-lighter text-slate-300 disabled:opacity-40 border border-surface-border transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
