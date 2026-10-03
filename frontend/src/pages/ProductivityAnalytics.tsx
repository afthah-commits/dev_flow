import React, { useEffect, useState } from 'react';
import { timeApi } from '../lib/timeApi';
import { ProductivityStats, TeamWorkload } from '../types/time';

export default function ProductivityAnalytics() {
  const [stats, setStats] = useState<ProductivityStats | null>(null);
  const [workload, setWorkload] = useState<TeamWorkload[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsData, workloadData] = await Promise.all([
        timeApi.getProductivityStats(),
        timeApi.getTeamWorkload()
      ]);
      setStats(statsData);
      setWorkload(workloadData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-gray-400">Loading analytics...</div>;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-white">Productivity Analytics</h1>

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
