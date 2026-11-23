import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  AlertCircle,
  FileText,
  Download,
  ExternalLink,
  CheckCircle,
  AlertTriangle,
  Info,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import { DataQualityReport } from '../types';
import { MetricCard } from '../components/MetricCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export const DataQualityPage: React.FC = () => {
  const [report, setReport] = useState<DataQualityReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDataQualityReport();
      setReport(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch Data Quality scorecard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, []);

  const downloadReportJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `retailiq_quality_report_${report.report_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <LoadingSpinner message="Auditing data quality scorecard..." />;
  if (error) return <ErrorAlert message={error} onRetry={loadReport} />;
  if (!report) return null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-mono flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-cyan-400" />
            Data Quality & Validation Governance
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Automated hygiene checks, anomaly detection audits, and mathematical health scoring.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <a
            href="/reports/eda_report.html"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium bg-surface-light hover:bg-surface-lighter text-slate-200 border border-surface-border rounded-md transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
            View Full HTML EDA Report
          </a>
          <button
            onClick={downloadReportJSON}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white rounded-md shadow transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            Export Audit JSON
          </button>
        </div>
      </div>

      {/* Main Health Scorecards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Overall Health Score"
          value={`${report.overall_quality_score}/100`}
          subValue={report.scoring_breakdown.formula}
          icon={ShieldCheck}
          badge={report.status}
          badgeType="success"
        />
        <MetricCard
          title="Completeness Index"
          value={`${report.scoring_breakdown.completeness_score}%`}
          subValue="Account & Description coverage"
          icon={CheckCircle}
        />
        <MetricCard
          title="Validity Index"
          value={`${report.scoring_breakdown.validity_score}%`}
          subValue="Positive price & commercial filter"
          icon={Layers}
        />
        <MetricCard
          title="Uniqueness Index"
          value={`${report.scoring_breakdown.uniqueness_score}%`}
          subValue="Exact duplicate row prevention"
          icon={FileText}
        />
      </div>

      {/* Anomaly Breakdown Grid */}
      <div className="bg-surface border border-surface-border rounded-lg p-6">
        <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-cyan-400" />
          Ingestion Anomaly Audit & Cleansing Actions Taken
        </h3>
        <p className="text-xs text-slate-400 mb-6">
          Every raw data discrepancy is audited deterministically to protect downstream analytical models.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-surface-light rounded-lg border border-surface-border">
            <span className="text-[11px] uppercase font-medium text-slate-400">Duplicate Records</span>
            <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
              {report.anomalies_detected.duplicate_rows.toLocaleString()}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Exact row repeats removed to prevent transaction double-counting.
            </p>
          </div>

          <div className="p-4 bg-surface-light rounded-lg border border-surface-border">
            <span className="text-[11px] uppercase font-medium text-slate-400">Cancellations Flagged</span>
            <div className="text-xl font-bold font-mono text-amber-400 mt-1">
              {report.anomalies_detected.cancellations_flagged.toLocaleString()}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Invoices prefixed with 'C' segregated from completed sales.
            </p>
          </div>

          <div className="p-4 bg-surface-light rounded-lg border border-surface-border">
            <span className="text-[11px] uppercase font-medium text-slate-400">Missing Customer IDs</span>
            <div className="text-xl font-bold font-mono text-blue-400 mt-1">
              {report.anomalies_detected.missing_customer_ids.toLocaleString()}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Preserved as guest purchases; excluded from identified RFM quintiles.
            </p>
          </div>

          <div className="p-4 bg-surface-light rounded-lg border border-surface-border">
            <span className="text-[11px] uppercase font-medium text-slate-400">Invalid Unit Prices</span>
            <div className="text-xl font-bold font-mono text-rose-400 mt-1">
              {report.anomalies_detected.invalid_or_zero_unit_prices.toLocaleString()}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Zero/negative unit prices (test or scrap adjustments) filtered out.
            </p>
          </div>
        </div>
      </div>

      {/* Summary Verification Ledger */}
      <div className="bg-surface border border-surface-border rounded-lg p-6">
        <h3 className="text-sm font-semibold text-white mb-4">
          Data Governance Verification Ledger
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs font-mono">
          <div className="space-y-3 bg-surface-light p-4 rounded border border-surface-border">
            <div className="flex justify-between border-b border-surface-border pb-2">
              <span className="text-slate-400">Report Reference:</span>
              <span className="text-cyan-400 font-bold">{report.report_id}</span>
            </div>
            <div className="flex justify-between border-b border-surface-border pb-2">
              <span className="text-slate-400">Ingested Raw Records:</span>
              <span className="text-white">{report.summary_metrics.raw_records.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-b border-surface-border pb-2">
              <span className="text-slate-400">Cleaned Valid Transactions:</span>
              <span className="text-emerald-400 font-bold">{report.summary_metrics.cleaned_records.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Data Retention Rate:</span>
              <span className="text-white font-bold">{report.summary_metrics.retention_rate_pct}%</span>
            </div>
          </div>

          <div className="space-y-3 bg-surface-light p-4 rounded border border-surface-border">
            <div className="flex justify-between border-b border-surface-border pb-2">
              <span className="text-slate-400">Total Valid Revenue:</span>
              <span className="text-white font-bold">
                £{report.summary_metrics.total_valid_revenue.toLocaleString('en-GB', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between border-b border-surface-border pb-2">
              <span className="text-slate-400">Active Product SKUs:</span>
              <span className="text-white">{report.summary_metrics.unique_products.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-b border-surface-border pb-2">
              <span className="text-slate-400">Identified Client Accounts:</span>
              <span className="text-white">{report.summary_metrics.unique_customers.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Temporal Coverage:</span>
              <span className="text-cyan-400">{report.temporal_coverage.total_days_active} Active Days</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
