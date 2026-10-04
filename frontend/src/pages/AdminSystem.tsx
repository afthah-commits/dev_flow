import React, { useEffect, useState } from 'react';
import { api } from '../lib/axios';
import { Server, Activity, ShieldAlert, Cpu } from 'lucide-react';

export default function AdminSystem() {
  const [stats, setStats] = useState<any>(null);
  const [jobStats, setJobStats] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/jobs/stats').then(res => setJobStats(res.data)).catch(err => console.error(err));
    api.get('/admin/system')
      .then(res => setStats(res.data))
      .catch(err => setError('Access denied or failed to load.'));
  }, []);

  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
  if (!stats) return <div className="p-8 text-center text-gray-500">Loading system stats...</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Server className="w-6 h-6 text-red-400" />
        System Administration
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Activity className="text-blue-400 w-5 h-5" /> Health
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-400">Database</span><span className="text-green-400">{stats.health.database}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Workers</span><span className="text-green-400">{stats.health.workers}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Integrations</span><span className="text-green-400">{stats.health.integrations}</span></div>
          </div>
        </div>
        
        <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Cpu className="text-purple-400 w-5 h-5" /> Background Jobs
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-400">Queued</span><span className="text-white">{stats.jobs.queued}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Running</span><span className="text-yellow-400">{stats.jobs.running}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Failed</span><span className="text-red-400">{stats.jobs.failed}</span></div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Activity className="text-green-400 w-5 h-5" /> API Performance
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-400">Avg Latency</span><span className="text-white">{stats.performance.average_latency_ms} ms</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Error Rate</span><span className="text-red-400">{stats.performance.error_rate_pct}%</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Req / Min</span><span className="text-white">{stats.performance.requests_per_minute}</span></div>
          </div>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
          <ShieldAlert className="text-yellow-400 w-5 h-5" /> Recent Security Events
        </h3>
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-800 text-gray-400">
            <tr>
              <th className="p-3">Time</th>
              <th className="p-3">Event Type</th>
              <th className="p-3">Actor</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {stats.recent_security_events.map((e: any) => (
              <tr key={e.id}>
                <td className="p-3">{new Date(e.created_at).toLocaleString()}</td>
                <td className="p-3 font-medium text-white">{e.type}</td>
                <td className="p-3 text-gray-400 text-xs">{e.actor || 'System'}</td>
              </tr>
            ))}
            {stats.recent_security_events.length === 0 && (
              <tr><td colSpan={3} className="p-3 text-center text-gray-500">No recent security events</td></tr>
            )}
          </tbody>
        </table>
      </div>
    
      <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg md:col-span-3 mt-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
          <Activity className="text-blue-400 w-5 h-5" /> Job Operations
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><div className="text-gray-500">Queue Depth</div><div className="text-xl text-white">{jobStats?.queue_depth || 0}</div></div>
            <div><div className="text-gray-500">24h Throughput</div><div className="text-xl text-white">{jobStats?.throughput_24h || 0}</div></div>
            <div><div className="text-gray-500">Success Rate</div><div className="text-xl text-green-400">{jobStats?.success_rate_24h || 0}%</div></div>
            <div><div className="text-gray-500">Failure Rate</div><div className="text-xl text-red-400">{jobStats?.failure_rate_24h || 0}%</div></div>
            <div><div className="text-gray-500">Avg Execution Time</div><div className="text-xl text-white">{jobStats?.avg_execution_time_sec || 0}s</div></div>
            <div><div className="text-gray-500">Active (Running)</div><div className="text-xl text-blue-400">{jobStats?.RUNNING || 0}</div></div>
            <div><div className="text-gray-500">Retrying</div><div className="text-xl text-yellow-400">{jobStats?.RETRYING || 0}</div></div>
        </div>
      </div>
</div>
  );
}