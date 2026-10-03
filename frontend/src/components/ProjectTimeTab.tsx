import React, { useEffect, useState } from 'react';
import { timeApi } from '../lib/timeApi';
import { ProjectTimeStats } from '../types/time';

export function ProjectTimeTab({ projectId }: { projectId: string }) {
  const [stats, setStats] = useState<ProjectTimeStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, [projectId]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await timeApi.getProjectStats(projectId);
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-gray-400">Loading time analytics...</div>;
  if (!stats) return <div className="p-8 text-red-400">Failed to load analytics</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div className="text-sm text-gray-400">Total Tracked</div>
          <div className="text-2xl font-bold text-white">{stats.total_tracked_hours.toFixed(1)}h</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div className="text-sm text-gray-400">Billable</div>
          <div className="text-2xl font-bold text-emerald-400">{stats.billable_hours.toFixed(1)}h</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div className="text-sm text-gray-400">Active Contributors</div>
          <div className="text-2xl font-bold text-white">{stats.active_users}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div className="text-sm text-gray-400">Tasks Tracked</div>
          <div className="text-2xl font-bold text-blue-400">{stats.tasks_tracked}</div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Estimates vs Actuals</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Estimated</span>
              <span className="text-white font-medium">{stats.estimated_hours.toFixed(1)}h</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Tracked</span>
              <span className="text-white font-medium">{stats.total_tracked_hours.toFixed(1)}h</span>
            </div>
            <div className="flex justify-between text-sm border-t border-gray-800 pt-2 mt-2">
              <span className="text-gray-400">Variance</span>
              <span className={`font-medium ${stats.estimate_variance > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {stats.estimate_variance > 0 ? '+' : ''}{stats.estimate_variance.toFixed(1)}h
              </span>
            </div>
          </div>
        </div>
        
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Averages</h3>
          <div className="space-y-4">
            <div>
              <div className="text-sm text-gray-400">Avg Time per Task</div>
              <div className="text-xl font-medium text-white">{stats.avg_time_per_task.toFixed(1)}h</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
