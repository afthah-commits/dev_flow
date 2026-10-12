import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { deliveryAnalyticsApi } from '../lib/deliveryAnalyticsApi';
import { DeliveryMetrics, DoraMetrics } from '../types/deliveryAnalytics';
import { Activity, BarChart2, RefreshCw, AlertCircle } from 'lucide-react';

const fallbackMetrics: DeliveryMetrics = {
  deployment_frequency: 0,
  successful_deployment_rate: 100,
  failed_deployment_rate: 0,
  avg_deployment_duration_seconds: 0,
  release_frequency: 0,
  avg_release_cycle_time_days: 0,
  pipeline_success_rate: 100,
  rollback_frequency: 0,
  avg_lead_time_days: 0
};

const fallbackDora: DoraMetrics = {
  deployment_frequency: 'Low (on-demand)',
  lead_time_for_changes: '< 1 day',
  change_failure_rate: '0%',
  mean_time_to_recovery: '< 1 hour'
};

export default function DeliveryAnalytics() {
  const [metrics, setMetrics] = useState<DeliveryMetrics | null>(null);
  const [dora, setDora] = useState<DoraMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    const [metricsRes, doraRes] = await Promise.allSettled([
      deliveryAnalyticsApi.getDeliveryMetrics(),
      deliveryAnalyticsApi.getDoraMetrics()
    ]);

    let loadedMetrics: DeliveryMetrics | null = null;
    let loadedDora: DoraMetrics | null = null;

    if (metricsRes.status === 'fulfilled') {
      loadedMetrics = metricsRes.value;
    } else {
      console.warn('Delivery metrics fetch failed:', metricsRes.reason);
    }

    if (doraRes.status === 'fulfilled') {
      loadedDora = doraRes.value;
    } else {
      console.warn('DORA metrics fetch failed:', doraRes.reason);
    }

    if (!loadedMetrics && !loadedDora) {
      setError('Unable to fetch delivery analytics. You may need higher organization role permissions.');
      setMetrics(fallbackMetrics);
      setDora(fallbackDora);
    } else {
      setMetrics(loadedMetrics || fallbackMetrics);
      setDora(loadedDora || fallbackDora);
    }

    setLoading(false);
  };

  const currentMetrics = metrics || fallbackMetrics;
  const currentDora = dora || fallbackDora;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2.5">
            <Activity className="w-7 h-7 text-purple-400" />
            Engineering Delivery Metrics
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time pipeline performance, cycle times, and DORA telemetry.
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 self-start sm:self-auto text-gray-400 hover:text-white bg-gray-900 border border-gray-800 rounded-lg hover:bg-gray-800 transition-colors"
          title="Refresh metrics"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Analytics Sub-tabs */}
      <div className="flex flex-wrap items-center gap-2 text-sm border-b border-gray-800 pb-3">
        <Link
          to="/analytics/productivity"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Productivity
        </Link>
        <Link
          to="/analytics/delivery"
          className="px-3 py-1.5 rounded-md font-medium bg-purple-600/20 text-purple-300 border border-purple-500/30"
        >
          Delivery & DORA
        </Link>
        <Link
          to="/analytics/collaboration"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Collaboration
        </Link>
        <Link
          to="/analytics/knowledge"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Knowledge Base
        </Link>
        <Link
          to="/analytics/workflows"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Workflows
        </Link>
      </div>

      {/* Loading */}
      {loading && (
        <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-12 text-center text-gray-400 space-y-3">
          <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-medium text-gray-300">Loading delivery telemetry...</p>
        </div>
      )}

      {/* Error alert notice */}
      {!loading && error && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center justify-between text-amber-300 text-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error} Showing baseline metrics.</span>
          </div>
          <button
            onClick={loadData}
            className="text-xs font-semibold text-white bg-amber-500/20 hover:bg-amber-500/30 px-3 py-1 rounded transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Main metrics display */}
      {!loading && (
        <div className="space-y-8">
          <div>
            <h2 className="text-lg font-bold text-white mb-4">Pipeline & Cycle Time</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard title="Release Frequency" value={currentMetrics.release_frequency} />
              <MetricCard title="Avg Cycle Time" value={`${(currentMetrics.avg_release_cycle_time_days ?? 0).toFixed(1)} days`} />
              <MetricCard title="Deployments" value={currentMetrics.deployment_frequency} />
              <MetricCard title="Pipeline Success" value={`${(currentMetrics.pipeline_success_rate ?? 0).toFixed(1)}%`} />
              <MetricCard title="Deployment Success" value={`${(currentMetrics.successful_deployment_rate ?? 0).toFixed(1)}%`} />
              <MetricCard title="Deployment Failure" value={`${(currentMetrics.failed_deployment_rate ?? 0).toFixed(1)}%`} />
              <MetricCard title="Rollbacks" value={currentMetrics.rollback_frequency ?? 0} />
              <MetricCard title="Lead Time (Tasks)" value={`${(currentMetrics.avg_lead_time_days ?? 0).toFixed(1)} days`} />
            </div>
          </div>

          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
              <BarChart2 className="w-5 h-5 text-blue-400" />
              DORA Metrics
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard title="Deployment Frequency" value={currentDora.deployment_frequency} />
              <MetricCard title="Lead Time for Changes" value={currentDora.lead_time_for_changes} />
              <MetricCard title="Change Failure Rate" value={currentDora.change_failure_rate} />
              <MetricCard title="Mean Time to Recovery" value={currentDora.mean_time_to_recovery} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-sm space-y-1">
      <div className="text-gray-400 text-xs font-medium">{title}</div>
      <div className="text-xl sm:text-2xl font-bold text-white tracking-tight">{value}</div>
    </div>
  );
}
