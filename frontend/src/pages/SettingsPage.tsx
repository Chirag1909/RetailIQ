import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Database,
  Upload,
  CheckCircle2,
  Server,
  Code,
  Info,
  ExternalLink,
} from 'lucide-react';
import { api } from '../services/api';
import { HealthStatus, PlatformMetadata } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [metadata, setMetadata] = useState<PlatformMetadata | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEnv = async () => {
      try {
        setLoading(true);
        const [h, m] = await Promise.all([api.getHealth(), api.getMetadata()]);
        setHealth(h);
        setMetadata(m);
      } catch (e) {
        // Handled gracefully
      } finally {
        setLoading(false);
      }
    };
    fetchEnv();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadResult(null);
      setUploadError(null);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    try {
      setIsUploading(true);
      setUploadError(null);
      const res = await api.uploadDataset(selectedFile);
      setUploadResult(res);
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail || err?.message || 'File upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  if (loading) return <LoadingSpinner message="Checking platform configuration..." />;

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white font-mono flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-cyan-400" />
          Platform Settings & Environment Architecture
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Operational configurations, database engine status, and custom dataset ingestion.
        </p>
      </div>

      {/* Database & Runtime Health */}
      <div className="bg-surface border border-surface-border rounded-lg p-6 space-y-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          Active Database Connection & Storage Subsystem
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-4 bg-surface-light rounded border border-surface-border space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Database Engine:</span>
              <span className="text-cyan-400 font-bold">PostgreSQL / SQLite Dual Dialect</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Connection Status:</span>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {health?.database_connected ? 'Connected & Healthy' : 'Degraded'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Star-Schema Tables:</span>
              <span className="text-white">13 Relational Entities</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Analytical SQL Views:</span>
              <span className="text-white">7 Operational Views</span>
            </div>
          </div>

          <div className="p-4 bg-surface-light rounded border border-surface-border space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Dataset Provenance:</span>
              <span className="text-slate-200 truncate max-w-[200px]">{metadata?.dataset_source}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Platform Version:</span>
              <span className="text-white">{metadata?.version}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Environment:</span>
              <span className="text-white font-bold">{health?.environment.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">FastAPI Documentation:</span>
              <a href="/docs" target="_blank" className="text-cyan-400 hover:underline flex items-center gap-1">
                Swagger UI <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Dataset Staging & Upload */}
      <div className="bg-surface border border-surface-border rounded-lg p-6 space-y-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Upload className="w-4 h-4 text-cyan-400" />
          Ingest Custom Retail Dataset (CSV or XLSX)
        </h3>
        <p className="text-xs text-slate-400">
          Upload new transactional batches. The file schema will be verified against the expected 8 standard fields before staging.
        </p>

        <form onSubmit={handleUploadSubmit} className="space-y-4">
          <div className="flex items-center gap-4">
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileChange}
              className="text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-surface-light file:text-cyan-400 hover:file:bg-surface-lighter cursor-pointer"
            />
            <button
              type="submit"
              disabled={!selectedFile || isUploading}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-semibold disabled:opacity-50 transition-colors"
            >
              {isUploading ? 'Verifying Schema...' : 'Upload & Validate'}
            </button>
          </div>

          {uploadError && (
            <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded text-xs text-rose-300">
              {uploadError}
            </div>
          )}

          {uploadResult && (
            <div className="p-4 bg-emerald-950/40 border border-emerald-800/60 rounded text-xs text-emerald-200 font-mono space-y-1">
              <div className="font-bold flex items-center gap-1.5 text-emerald-300">
                <CheckCircle2 className="w-4 h-4" /> {uploadResult.message}
              </div>
              <p>Staged File: {uploadResult.file_name}</p>
              <p>Columns: {uploadResult.columns_detected.join(', ')}</p>
            </div>
          )}
        </form>
      </div>

      {/* Supported ML Models Catalog */}
      <div className="bg-surface border border-surface-border rounded-lg p-6 space-y-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Code className="w-4 h-4 text-cyan-400" />
          Integrated Time-Series Forecasting Models
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 bg-surface-light rounded border border-surface-border space-y-1">
            <span className="font-semibold text-cyan-400">1. Seasonal Naive Baseline</span>
            <p className="text-slate-400">Projects 7-day cyclical weekly periodicity with zero latency.</p>
          </div>
          <div className="p-4 bg-surface-light rounded border border-surface-border space-y-1">
            <span className="font-semibold text-blue-400">2. Holt-Winters Smoothing</span>
            <p className="text-slate-400">Additive trend and seasonal smoothing via Statsmodels ETS.</p>
          </div>
          <div className="p-4 bg-surface-light rounded border border-surface-border space-y-1">
            <span className="font-semibold text-emerald-400">3. XGBoost Forecaster</span>
            <p className="text-slate-400">Lag 1/7/14/28, rolling stats, and calendar features.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
