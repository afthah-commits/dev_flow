import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { timeApi } from '../lib/timeApi';
import { ProductivityStats, TeamWorkload } from '../types/time';
import { TrendingUp, RefreshCw } from 'lucide-react';

export default function ProductivityAnalytics() {
  const [stats, setStats] = useState<ProductivityStats | null>(null);
  const [workload, setWorkload] = useState<TeamWorkload[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const [error, setError] = useState(false);

  const loadData = async () => {
    // Load stats and workload independently so a workload failure cannot
    // blank the whole page.
    const [statsRes, workloadRes] = await Promise.allSettled([
      timeApi.getProductivityStats(),
      timeApi.getTeamWorkload()
    ]);
    if (statsRes.status === 'fulfilled') {
      setStats(statsRes.value);
    } else {
      console.error(statsRes.reason);
      setError(true);
    }
    if (workloadRes.status === 'fulfilled') {
      setWorkload(workloadRes.value);
    } else {
      console.error(workloadRes.reason);
    }
    setLoading(false);
  };

  if (loading) return <div className="p-8 text-gray-400">Loading analytics...</div>;

  if (error && !stats) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-400">Failed to load productivity analytics.</p>
        <button
          onClick={() => { setLoading(true); setError(false); loadData(); }}
          className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2.5">
            <TrendingUp className="w-7 h-7 text-blue-400" />
            Productivity Analytics
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Developer velocity, tracked hours, and sprint completion metrics.
          </p>
        </div>
        <button
          onClick={() => { setLoading(true); setError(false); loadData(); }}
          className="p-2 self-start sm:self-auto text-gray-400 hover:text-white bg-gray-900 border border-gray-800 rounded-lg hover:bg-gray-800 transition-colors"
          title="Refresh analytics"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Analytics Sub-tabs */}
      <div className="flex flex-wrap items-center gap-2 text-sm border-b border-gray-800 pb-3">
        <Link
          to="/analytics/productivity"
          className="px-3 py-1.5 rounded-md font-medium bg-blue-600/20 text-blue-300 border border-blue-500/30"
        >
          Productivity
        </Link>
        <Link
          to="/analytics/delivery"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
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

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400">Total Tracked</div>
            <div className="text-2xl font-bold text-white">{stats.total_hours.toFixed(1)}h</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400">Avg Hours / Day</div>
            <div className="text-2xl font-bold text-blue-400">{stats.avg_hours_per_day.toFixed(1)}h</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400">Tasks Completed</div>
            <div className="text-2xl font-bold text-emerald-400">{stats.tasks_completed}</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400">Completion Rate</div>
            <div className="text-2xl font-bold text-white">{stats.completion_rate.toFixed(0)}%</div>
          </div>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Team Workload</h2>
        <div className="space-y-4">
          {workload.map(member => (
            <div key={member.user_id} className="border-b border-gray-800 pb-4 last:border-0 last:pb-0">
              <div className="flex justify-between items-end mb-2">
                <div>
                  <div className="font-medium text-white">{member.user_name}</div>
                  <div className="text-sm text-gray-400">
                    {member.tracked_hours.toFixed(1)}h tracked · {member.completed_tasks}/{member.assigned_tasks} tasks completed
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-medium ${member.workload_percentage > 100 ? 'text-red-400' : 'text-blue-400'}`}>
                    {member.workload_percentage.toFixed(0)}% Workload
                  </div>
                </div>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${member.workload_percentage > 100 ? 'bg-red-500' : 'bg-blue-500'}`}
                  style={{ width: `${Math.min(member.workload_percentage, 100)}%` }}
                ></div>
              </div>
            </div>
          ))}
          {workload.length === 0 && (
            <div className="text-gray-500">No team workload data found.</div>
          )}
        </div>
      </div>
    </div>
  );
}
