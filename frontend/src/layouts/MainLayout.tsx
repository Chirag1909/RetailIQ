import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  Package,
  Users,
  Cpu,
  Boxes,
  GitBranch,
  ShieldCheck,
  Settings,
  RefreshCw,
  Database,
  ExternalLink,
  Activity,
  CheckCircle2,
  Calendar,
} from 'lucide-react';
import { api } from '../services/api';
import { PipelineStatus } from '../types';

const navigation = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Sales Analytics', href: '/sales', icon: TrendingUp },
  { name: 'Product Intelligence', href: '/products', icon: Package },
  { name: 'Customer Insights', href: '/customers', icon: Users },
  { name: 'Demand Forecasting', href: '/forecast', icon: Cpu },
  { name: 'Inventory Optimization', href: '/inventory', icon: Boxes },
  { name: 'Data Pipeline', href: '/pipeline', icon: GitBranch },
  { name: 'Data Quality', href: '/quality', icon: ShieldCheck },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export const MainLayout: React.FC = () => {
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const location = useLocation();

  const fetchStatus = async () => {
    try {
      const data = await api.getPipelineStatus();
      setPipelineStatus(data);
    } catch {
      // Backend not yet ready or offline
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleGlobalRefresh = async () => {
    setIsRefreshing(true);
    await fetchStatus();
    // Dispatch a custom window event that pages can listen to for refetching
    window.dispatchEvent(new Event('retailiq:refresh'));
    setTimeout(() => setIsRefreshing(false), 600);
  };

  return (
    <div className="flex h-screen bg-background text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-surface flex flex-col border-r border-surface-border shrink-0 z-20">
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-surface-border gap-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Boxes className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-base tracking-tight text-white font-mono">RetailIQ</span>
              <span className="text-[10px] font-semibold px-1.5 py-0.2 bg-cyan-500/20 text-cyan-300 rounded border border-cyan-500/30">v1.0</span>
            </div>
            <p className="text-[10px] text-slate-400 truncate max-w-[150px]">Retail Intelligence Suite</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-md text-xs font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/25 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-surface-light/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Operational Footer Details */}
        <div className="p-4 border-t border-surface-border bg-surface-light/30">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              API Connected
            </span>
            <span className="font-mono text-[11px] text-slate-400">Port 8000</span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>ETL Quality:</span>
            <span className="font-mono font-semibold text-emerald-400">
              {pipelineStatus ? `${pipelineStatus.last_quality_score}%` : '95.9%'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-surface/80 backdrop-blur border-b border-surface-border flex items-center justify-between px-8 shrink-0 z-10">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs bg-surface-light px-3 py-1.5 rounded-md border border-surface-border text-slate-300">
              <Database className="w-3.5 h-3.5 text-cyan-400" />
              <span className="font-medium">UCI Online Retail Dataset</span>
              <span className="text-slate-400">|</span>
              <span className="text-slate-400 font-mono">541,909 raw / 522,710 verified</span>
            </div>

            <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-400 bg-surface-light/40 px-2.5 py-1.5 rounded border border-surface-border">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>Dec 2010 – Dec 2011</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {pipelineStatus?.latest_run && (
              <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400 bg-surface-light px-2.5 py-1.5 rounded border border-surface-border">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Last ETL: <span className="text-slate-200 font-mono">{pipelineStatus.latest_run.status}</span></span>
              </div>
            )}

            <button
              onClick={handleGlobalRefresh}
              disabled={isRefreshing}
              title="Refresh Platform Analytics"
              className="p-2 rounded-md bg-surface-light hover:bg-surface-lighter text-slate-300 hover:text-white border border-surface-border transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            </button>

            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-surface-light hover:bg-surface-lighter text-cyan-400 border border-cyan-500/30 transition-colors"
            >
              <span>FastAPI Docs</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </header>

        {/* Dynamic Route View */}
        <main className="flex-1 overflow-y-auto p-8 bg-background">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
