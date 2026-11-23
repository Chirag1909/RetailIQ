import React, { useState, useEffect } from 'react';
import {
  Boxes,
  AlertTriangle,
  ShieldAlert,
  Clock,
  Edit2,
  CheckCircle,
  Search,
  Filter,
  Save,
  X,
  Info,
} from 'lucide-react';
import { api } from '../services/api';
import { InventoryOverview, InventoryItem } from '../types';
import { MetricCard } from '../components/MetricCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export const InventoryPage: React.FC = () => {
  const [overview, setOverview] = useState<InventoryOverview | null>(null);
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [editForm, setEditForm] = useState({
    current_stock: 100,
    lead_time_days: 14,
    service_level_pct: 95.0,
    holding_cost: 1.5,
    reorder_cost: 25.0,
  });
  const [isUpdating, setIsUpdating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (risk?: string, search?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getInventoryOverview(risk, search, 50);
      setOverview(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load inventory parameters.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFilterChange = (r: string) => {
    setRiskFilter(r);
    loadData(r, searchTerm);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData(riskFilter, searchTerm);
  };

  const openEditModal = (item: InventoryItem) => {
    setEditingItem(item);
    setEditForm({
      current_stock: item.current_stock,
      lead_time_days: item.lead_time_days,
      service_level_pct: item.service_level_pct,
      holding_cost: 1.5,
      reorder_cost: 25.0,
    });
  };

  const handleSaveParameters = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingItem) return;

    try {
      setIsUpdating(true);
      const updated = await api.updateInventoryParameters(editingItem.stock_code, editForm);
      setEditingItem(null);
      // Reload inventory list
      await loadData(riskFilter, searchTerm);
    } catch (err: any) {
      alert(`Failed to update parameters: ${err?.message || 'Unknown error'}`);
    } finally {
      setIsUpdating(false);
    }
  };

  if (loading && !overview) return <LoadingSpinner message="Evaluating inventory replenishment models..." />;
  if (error && !overview) return <ErrorAlert message={error} onRetry={() => loadData()} />;
  if (!overview) return null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white font-mono flex items-center gap-2">
          <Boxes className="w-6 h-6 text-cyan-400" />
          Inventory Optimization & Reorder Decisions
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Safety stock sizing, expected lead-time demand, and stockout risk classifications.
        </p>
      </div>

      {/* Dataset Limitation Disclosure Alert */}
      <div className="bg-surface-light border border-cyan-500/30 rounded-lg p-4 text-xs text-slate-300 flex items-start gap-3">
        <Info className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
        <div>
          <span className="font-semibold text-cyan-300">Operational Assumption Note: </span>
          The UCI Online Retail dataset contains transaction history but does not contain physical warehouse levels or supplier lead times. Current stock, lead time, and service level targets are user-configured or simulated assumptions to facilitate decision support calculations.
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Critical Buffer Breaches"
          value={overview.critical_stockout_count}
          subValue="Immediate purchase order needed"
          icon={ShieldAlert}
          badge="Urgent"
          badgeType="danger"
        />
        <MetricCard
          title="Reorder Point Approached"
          value={overview.high_stockout_count}
          subValue="Replenishment cycle triggered"
          icon={AlertTriangle}
          badge="High Risk"
          badgeType="warning"
        />
        <MetricCard
          title="Avg Inventory Coverage"
          value={`${overview.average_coverage_days} Days`}
          subValue="Mean days of demand covered"
          icon={Clock}
        />
        <MetricCard
          title="Overstock Risks"
          value={overview.overstock_risk_count}
          subValue=">90 days of holding stock"
          icon={Boxes}
        />
      </div>

      {/* Inventory Items Table */}
      <div className="bg-surface border border-surface-border rounded-lg p-6 space-y-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <Filter className="w-3.5 h-3.5 text-cyan-400" />
              <span>Stockout Risk:</span>
            </div>
            <select
              value={riskFilter}
              onChange={(e) => handleFilterChange(e.target.value)}
              className="bg-surface-light border border-surface-border text-xs text-slate-200 rounded px-3 py-1.5 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Risk Tiers</option>
              <option value="Critical">Critical (Below Safety Stock)</option>
              <option value="High">High (Below ROP)</option>
              <option value="Medium">Medium (Approaching ROP)</option>
              <option value="Low">Low (Healthy Buffer)</option>
            </select>
          </div>

          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full md:w-72">
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search SKU or description..."
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

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-surface-border text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">SKU</th>
                <th className="py-3 px-4">Description</th>
                <th className="py-3 px-4 text-right">Current Stock</th>
                <th className="py-3 px-4 text-right">Safety Stock</th>
                <th className="py-3 px-4 text-right">Reorder Point</th>
                <th className="py-3 px-4 text-right">Suggested Order</th>
                <th className="py-3 px-4 text-right">Coverage</th>
                <th className="py-3 px-4 text-center">Stockout Risk</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border font-mono">
              {overview.inventory_items.map((item) => {
                const riskBadge = {
                  Critical: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
                  High: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
                  Medium: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
                  Low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
                }[item.stockout_risk_level] || 'bg-slate-700 text-slate-400';

                return (
                  <tr key={item.stock_code} className="hover:bg-surface-light/40 transition-colors">
                    <td className="py-3 px-4 font-semibold text-cyan-400">{item.stock_code}</td>
                    <td className="py-3 px-4 text-slate-200 font-sans max-w-xs truncate">{item.description}</td>
                    <td className="py-3 px-4 text-right font-bold text-white">{item.current_stock}</td>
                    <td className="py-3 px-4 text-right text-slate-300">{item.safety_stock}</td>
                    <td className="py-3 px-4 text-right text-slate-300">{item.reorder_point}</td>
                    <td className="py-3 px-4 text-right font-bold text-cyan-300">
                      {item.suggested_reorder_qty > 0 ? `+${item.suggested_reorder_qty}` : '0'}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">{item.inventory_coverage_days}d</td>
                    <td className="py-3 px-4 text-center font-sans">
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${riskBadge}`}>
                        {item.stockout_risk_level}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-sans">
                      <button
                        onClick={() => openEditModal(item)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded bg-surface-light hover:bg-surface-lighter text-slate-300 hover:text-white border border-surface-border transition-colors"
                      >
                        <Edit2 className="w-3 h-3 text-cyan-400" />
                        Tune
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Parameters Modal */}
      {editingItem && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-surface-border rounded-lg max-w-md w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-surface-border pb-3">
              <div>
                <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
                  <Edit2 className="w-4 h-4 text-cyan-400" />
                  Tune Inventory Parameters
                </h3>
                <p className="text-xs text-cyan-400 font-mono mt-0.5">{editingItem.stock_code} — {editingItem.description}</p>
              </div>
              <button
                onClick={() => setEditingItem(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveParameters} className="space-y-4 text-xs font-sans">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Current On-Hand Stock (units)</label>
                <input
                  type="number"
                  min="0"
                  value={editForm.current_stock}
                  onChange={(e) => setEditForm({ ...editForm, current_stock: parseInt(e.target.value) || 0 })}
                  className="w-full bg-surface-light border border-surface-border rounded px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Supplier Lead Time (days)</label>
                  <input
                    type="number"
                    min="1"
                    max="180"
                    value={editForm.lead_time_days}
                    onChange={(e) => setEditForm({ ...editForm, lead_time_days: parseInt(e.target.value) || 1 })}
                    className="w-full bg-surface-light border border-surface-border rounded px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Target Service Level (%)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="80"
                    max="99.9"
                    value={editForm.service_level_pct}
                    onChange={(e) => setEditForm({ ...editForm, service_level_pct: parseFloat(e.target.value) || 95 })}
                    className="w-full bg-surface-light border border-surface-border rounded px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
              </div>

              <div className="p-3 bg-surface-light rounded text-[11px] text-slate-400 space-y-1">
                <p>Calculates dynamic Safety Stock via Z-score of {editForm.service_level_pct}% service level.</p>
                <p>Reorder Point (ROP) = (Daily Demand x Lead Time) + Safety Stock.</p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-surface-border">
                <button
                  type="button"
                  onClick={() => setEditingItem(null)}
                  className="px-4 py-2 bg-surface-light hover:bg-surface-lighter text-slate-300 rounded font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUpdating}
                  className="flex items-center gap-1.5 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-medium transition-colors disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  {isUpdating ? 'Recalculating...' : 'Save & Recalculate'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
