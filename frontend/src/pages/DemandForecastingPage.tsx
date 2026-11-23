import React, { useState, useEffect } from 'react';
import {
  Cpu,
  TrendingUp,
  Download,
  Calendar,
  Layers,
  Award,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { api } from '../services/api';
import {
  ForecastResponse,
  ForecastAccuracyResponse,
} from '../types';
import { MetricCard } from '../components/MetricCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export const DemandForecastingPage: React.FC = () => {
  const [targetType, setTargetType] = useState('GLOBAL_REVENUE');
  const [targetIdentifier, setTargetIdentifier] = useState('ALL');
  const [horizonDays, setHorizonDays] = useState(30);

  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [accuracyData, setAccuracyData] = useState<ForecastAccuracyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadForecast = async () => {
    try {
      setLoading(true);
      setError(null);
      const [fRes, aRes] = await Promise.all([
        api.getForecast(targetType, targetIdentifier, horizonDays),
        api.getForecastAccuracy(targetIdentifier),
      ]);
      setForecastData(fRes);
      setAccuracyData(aRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to load forecast predictions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecast();
  }, [targetType, targetIdentifier, horizonDays]);

  const handleTargetChange = (val: string) => {
    if (val === 'ALL') {
      setTargetType('GLOBAL_REVENUE');
      setTargetIdentifier('ALL');
    } else {
      setTargetType('PRODUCT_DEMAND');
      setTargetIdentifier(val);
    }
  };

  const exportForecastCSV = () => {
    if (!forecastData || forecastData.forecasts.length === 0) return;
    const headers = ['Forecast Date', 'Predicted Value', 'Lower Bound (95%)', 'Upper Bound (95%)', 'Model Name'];
    const rows = forecastData.forecasts.map((pt) => [
      pt.forecast_date,
      pt.predicted_value,
      pt.lower_bound ?? '',
      pt.upper_bound ?? '',
      forecastData.model_name,
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `forecast_${targetIdentifier}_${horizonDays}days.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Combine historical baseline + forecast points for seamless Recharts line
  const chartData = React.useMemo(() => {
    if (!forecastData) return [];
    const history = (forecastData.historical_baseline || []).map((h) => ({
      date: h.date,
      actual: h.actual,
      forecast: null,
      lower: null,
      upper: null,
    }));

    const future = forecastData.forecasts.map((f) => ({
      date: f.forecast_date,
      actual: null,
      forecast: f.predicted_value,
      lower: f.lower_bound,
      upper: f.upper_bound,
    }));

    return [...history, ...future];
  }, [forecastData]);

  return (
    <div className="space-y-8">
      {/* Page Title & Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-mono flex items-center gap-2">
            <Cpu className="w-6 h-6 text-cyan-400" />
            Demand Forecasting Engine
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Genuine multi-horizon time-series forecasting with statistical confidence intervals.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Target Selector */}
          <div className="flex items-center gap-2 bg-surface-light px-3 py-1.5 rounded border border-surface-border text-xs">
            <span className="text-slate-400">Target:</span>
            <select
              value={targetIdentifier}
              onChange={(e) => handleTargetChange(e.target.value)}
              className="bg-transparent text-cyan-300 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="ALL">Enterprise Daily Revenue</option>
              <option value="22423">SKU 22423 (Regency Cakestand)</option>
              <option value="85123A">SKU 85123A (White Hanging Heart)</option>
              <option value="85099B">SKU 85099B (Jumbo Bag Retrospot)</option>
              <option value="47566">SKU 47566 (Party Bunting)</option>
            </select>
          </div>

          {/* Horizon Selector */}
          <div className="flex items-center gap-1 bg-surface-light p-1 rounded border border-surface-border text-xs">
            {[7, 30, 90].map((h) => (
              <button
                key={h}
                onClick={() => setHorizonDays(h)}
                className={`px-3 py-1 rounded font-medium transition-colors ${
                  horizonDays === h
                    ? 'bg-cyan-500 text-white font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {h}D
              </button>
            ))}
          </div>

          <button
            onClick={exportForecastCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-light hover:bg-surface-lighter text-cyan-400 border border-cyan-500/30 rounded text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" /> Export CSV
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Calculating recursive multi-step forecasting features..." />
      ) : error ? (
        <ErrorAlert message={error} onRetry={loadForecast} />
      ) : forecastData ? (
        <>
          {/* Champion Model Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Champion Model"
              value={forecastData.model_name}
              subValue="Selected via chronological validation"
              icon={Award}
              badge="Best Performer"
              badgeType="success"
            />
            <MetricCard
              title="WAPE (Validation)"
              value={`${forecastData.wape?.toFixed(2)}%`}
              subValue="Weighted Absolute % Error"
              icon={TrendingUp}
              badge={forecastData.wape && forecastData.wape < 40 ? 'Excellent' : 'Standard'}
              badgeType="info"
            />
            <MetricCard
              title="RMSE Error"
              value={
                targetType === 'GLOBAL_REVENUE'
                  ? `£${forecastData.rmse?.toLocaleString(undefined, { maximumFractionDigits: 1 })}`
                  : `${forecastData.rmse?.toFixed(1)} units`
              }
              subValue="Root Mean Squared Error"
              icon={AlertCircle}
            />
            <MetricCard
              title="Forecast Horizon"
              value={`${forecastData.horizon_days} Days`}
              subValue={`Ending ${forecastData.forecasts[forecastData.forecasts.length - 1]?.forecast_date}`}
              icon={Calendar}
            />
          </div>

          {/* Actual vs Forecast Interactive Chart */}
          <div className="bg-surface border border-surface-border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  Actual vs. Predicted Trajectory (with 95% Confidence Bounds)
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Historical signal transitioned to forward-looking multi-day projection.
                </p>
              </div>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                  <defs>
                    <linearGradient id="boundsFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e2e4f" vertical={false} />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis
                    stroke="#64748b"
                    fontSize={11}
                    tickLine={false}
                    tickFormatter={(v) => (targetType === 'GLOBAL_REVENUE' ? `£${(v / 1000).toFixed(0)}k` : `${v}`)}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0d1527', borderColor: '#1e2e4f', borderRadius: '6px' }}
                    labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                    formatter={(val: any, name: string) => [
                      targetType === 'GLOBAL_REVENUE' ? `£${Number(val).toLocaleString()}` : `${Number(val).toFixed(1)} units`,
                      name,
                    ]}
                  />
                  <Legend wrapperStyle={{ paddingTop: '10px' }} />
                  {/* Confidence Interval Upper/Lower Area */}
                  <Area
                    type="monotone"
                    dataKey="upper"
                    name="Upper Bound (95%)"
                    stroke="#38bdf8"
                    strokeDasharray="3 3"
                    fill="url(#boundsFill)"
                  />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Observed Actual"
                    stroke="#94a3b8"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="forecast"
                    name="Model Forecast"
                    stroke="#06b6d4"
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: '#06b6d4' }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Model Leaderboard Section */}
          {accuracyData && (
            <div className="bg-surface border border-surface-border rounded-lg p-6">
              <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
                <Award className="w-4 h-4 text-cyan-400" />
                Competitive Model Evaluation Leaderboard
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Rigorous chronological out-of-time test evaluation preventing data leakage.
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-surface-border text-slate-400 uppercase tracking-wider text-[11px]">
                      <th className="py-3 px-4">Model Architecture</th>
                      <th className="py-3 px-4 text-right">MAE</th>
                      <th className="py-3 px-4 text-right">RMSE</th>
                      <th className="py-3 px-4 text-right">MAPE (%)</th>
                      <th className="py-3 px-4 text-right">WAPE (%)</th>
                      <th className="py-3 px-4 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-border font-mono">
                    {accuracyData.leaderboard.map((m) => (
                      <tr
                        key={m.model_name}
                        className={`hover:bg-surface-light/40 transition-colors ${
                          m.is_champion ? 'bg-cyan-500/5' : ''
                        }`}
                      >
                        <td className="py-3 px-4 font-sans font-medium text-slate-200 flex items-center gap-2">
                          {m.model_name}
                          {m.is_champion && (
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              Selected Champion
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right text-slate-300">{m.mae.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-slate-300">{m.rmse.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-slate-300">{m.mape.toFixed(2)}%</td>
                        <td className="py-3 px-4 text-right font-bold text-cyan-400">{m.wape.toFixed(2)}%</td>
                        <td className="py-3 px-4 text-center">
                          {m.is_champion ? (
                            <span className="text-emerald-400 font-semibold">Active In Production</span>
                          ) : (
                            <span className="text-slate-500">Benchmark Evaluated</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Forecast Predictions Table */}
          <div className="bg-surface border border-surface-border rounded-lg p-6">
            <h3 className="text-sm font-semibold text-white mb-4">
              Upcoming Forecast Schedule ({forecastData.forecasts.length} Day Schedule)
            </h3>
            <div className="overflow-x-auto max-h-72">
              <table className="w-full text-left text-xs font-mono">
                <thead className="sticky top-0 bg-surface">
                  <tr className="border-b border-surface-border text-slate-400 uppercase tracking-wider text-[11px]">
                    <th className="py-2.5 px-4">Date</th>
                    <th className="py-2.5 px-4 text-right">Forecast Demand</th>
                    <th className="py-2.5 px-4 text-right">Lower Bound (95%)</th>
                    <th className="py-2.5 px-4 text-right">Upper Bound (95%)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {forecastData.forecasts.map((pt) => (
                    <tr key={pt.forecast_date} className="hover:bg-surface-light/30">
                      <td className="py-2 px-4 text-cyan-400">{pt.forecast_date}</td>
                      <td className="py-2 px-4 text-right font-bold text-white">
                        {targetType === 'GLOBAL_REVENUE'
                          ? `£${pt.predicted_value.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`
                          : `${pt.predicted_value.toFixed(1)} units`}
                      </td>
                      <td className="py-2 px-4 text-right text-slate-400">
                        {pt.lower_bound != null ? pt.lower_bound.toLocaleString() : '-'}
                      </td>
                      <td className="py-2 px-4 text-right text-slate-400">
                        {pt.upper_bound != null ? pt.upper_bound.toLocaleString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
