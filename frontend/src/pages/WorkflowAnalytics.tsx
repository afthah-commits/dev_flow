import React, { useCallback, useEffect, useState } from 'react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, LineChart, Line,
} from 'recharts';
import { workflowApi } from '../lib/workflowApi';

interface AnalyticsData {
  total_workflows: number;
  published_workflows: number;
  draft_workflows: number;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  active_executions: number;
  avg_execution_seconds: number | null;
  failure_rate: number | null;
  approval_rejection_rate: number | null;
  most_used_workflow: Record<string, any> | null;
  most_used_transition: Record<string, any> | null;
  state_durations: Record<string, any>[];
  executions_by_day: Record<string, any>[];
}

interface WorkflowListItem {
  id: string;
  name: string;
}

const COLORS = ['#3b82f6', '#22c55e', '#ef4444', '#a855f7', '#f59e0b', '#14b8a6'];

export const WorkflowAnalytics: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    workflowApi.list()
      .then((res) => {
        const items = res as WorkflowListItem[];
        setWorkflows(items);
        if (items.length) setSelected(items[0].id);
      })
      .catch(() => setError('Failed to load workflows'))
      .finally(() => setLoading(false));
  }, []);

  const load = useCallback(async () => {
    if (!selected) return;
    try {
      setData(await workflowApi.getAnalytics(selected));
      setError(null);
    } catch {
      setError('Failed to load analytics');
    }
  }, [selected]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="p-6 text-gray-400">Loading analytics…</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Workflow Analytics</h1>
          <p className="text-sm text-gray-400">Execution health, throughput, and process bottlenecks.</p>
        </div>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="rounded border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100"
        >
          {workflows.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
      </div>

      {error && <div className="mb-4 rounded border border-red-800 bg-red-900/30 px-3 py-2 text-sm text-red-200">{error}</div>}

      {!data ? (
        <div className="rounded border border-dashed border-gray-700 p-10 text-center text-gray-400">
          {workflows.length ? 'Select a workflow to view analytics.' : 'No workflows available yet.'}
        </div>
      ) : (
        <>
          <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            {[
              { label: 'Executions', value: data.total_executions },
              { label: 'Successful', value: data.successful_executions },
              { label: 'Failed', value: data.failed_executions },
              { label: 'Avg Time (s)', value: data.avg_execution_seconds != null ? data.avg_execution_seconds.toFixed(1) : '—' },
              { label: 'Failure Rate', value: data.failure_rate != null ? `${(data.failure_rate * 100).toFixed(0)}%` : '—' },
              { label: 'Approval Rejections', value: data.approval_rejection_rate != null ? `${(data.approval_rejection_rate * 100).toFixed(0)}%` : '—' },
              { label: 'Published / Draft', value: `${data.published_workflows} / ${data.draft_workflows}` },
              { label: 'Most Used Transition', value: data.most_used_transition?.name || '—' },
            ].map((c) => (
              <div key={c.label} className="rounded-lg border border-gray-800 bg-gray-900 p-4">
                <div className="text-xs text-gray-500">{c.label}</div>
                <div className="mt-1 text-xl font-bold text-white">{c.value}</div>
              </div>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
              <h3 className="mb-3 text-sm font-semibold text-gray-200">Execution Outcomes</h3>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={[
                  { name: 'Completed', value: data.successful_executions },
                  { name: 'Failed', value: data.failed_executions },
                  { name: 'Active', value: data.active_executions },
                ]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
                  <YAxis allowDecimals={false} stroke="#9ca3af" fontSize={12} />
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151' }} />
                  <Bar dataKey="value" name="Executions">
                    <Cell fill="#22c55e" /><Cell fill="#ef4444" /><Cell fill="#3b82f6" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
              <h3 className="mb-3 text-sm font-semibold text-gray-200">State Duration (visits per state)</h3>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={data.state_durations.length ? data.state_durations : [{ state: 'No data', count: 1 }]}
                    dataKey="count" nameKey="state" outerRadius={90} label
                  >
                    {(data.state_durations.length ? data.state_durations : [{ state: 'No data', count: 1 }]).map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151' }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default WorkflowAnalytics;
