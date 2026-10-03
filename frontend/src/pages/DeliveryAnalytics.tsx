import React, { useEffect, useState } from 'react';
import { deliveryAnalyticsApi } from '../lib/deliveryAnalyticsApi';
import { DeliveryMetrics, DoraMetrics } from '../types/deliveryAnalytics';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, BarChart2 } from 'lucide-react';

export default function DeliveryAnalytics() {
  const [metrics, setMetrics] = useState<DeliveryMetrics | null>(null);
  const [dora, setDora] = useState<DoraMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      deliveryAnalyticsApi.getDeliveryMetrics(),
      deliveryAnalyticsApi.getDoraMetrics()
    ]).then(([m, d]) => {
      setMetrics(m);
      setDora(d);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-500">Loading metrics...</div>;
  if (!metrics || !dora) return null;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-6">
          <Activity className="w-6 h-6 text-purple-400" />
          Engineering Delivery Metrics
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <MetricCard title="Release Frequency" value={metrics.release_frequency} />
          <MetricCard title="Avg Cycle Time" value={`${metrics.avg_release_cycle_time_days.toFixed(1)} days`} />
          <MetricCard title="Deployments" value={metrics.deployment_frequency} />
          <MetricCard title="Pipeline Success" value={`${metrics.pipeline_success_rate.toFixed(1)}%`} />
          <MetricCard title="Success Rate" value={`${metrics.successful_deployment_rate.toFixed(1)}%`} />
          <MetricCard title="Failure Rate" value={`${metrics.failed_deployment_rate.toFixed(1)}%`} />
          <MetricCard title="Rollbacks" value={metrics.rollback_frequency} />
          <MetricCard title="Lead Time (Tasks)" value={`${metrics.avg_lead_time_days.toFixed(1)} days`} />
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
          <BarChart2 className="w-5 h-5 text-blue-400" />
          DORA-style Metrics
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard title="Deployment Frequency" value={dora.deployment_frequency} />
          <MetricCard title="Lead Time for Changes" value={dora.lead_time_for_changes} />
          <MetricCard title="Change Failure Rate" value={dora.change_failure_rate} />
          <MetricCard title="Mean Time to Recovery" value={dora.mean_time_to_recovery} />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value }: { title: string, value: string | number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <div className="text-gray-400 text-sm mb-1">{title}</div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}
