import React, { useEffect, useState } from 'react';
import { analyticsApi } from '../lib/analyticsApi';
import { ProjectAnalyticsResponse, GitHubAnalyticsResponse } from '../types/analytics';
import { Project } from '../types/project';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface Props {
  project: Project;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export function ProjectAnalytics({ project }: Props) {
  const [analytics, setAnalytics] = useState<ProjectAnalyticsResponse | null>(null);
  const [gh, setGh] = useState<GitHubAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.getProjectAnalytics(project.id).then(setAnalytics).catch(() => {}),
      analyticsApi.getGitHubAnalytics(project.id).then(setGh).catch(() => {})
    ]).finally(() => setLoading(false));
  }, [project.id]);

  if (loading) return <div className="p-6 text-gray-400">Loading analytics...</div>;
  if (!analytics) return <div className="p-6 text-red-400">Failed to load analytics</div>;

  const pieData = analytics.status_distribution.map((d, i) => ({
    name: d.status,
    value: d.count,
    color: COLORS[i % COLORS.length]
  }));

  return (
    <div className="space-y-6">
      {/* Top Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
          <div className="text-gray-400 text-sm">Completion Rate</div>
          <div className="text-3xl font-bold text-white mt-1">{analytics.completion_rate.toFixed(1)}%</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
          <div className="text-gray-400 text-sm">Health Score</div>
          <div className={`text-3xl font-bold mt-1 ${analytics.health.score < 50 ? 'text-red-500' : analytics.health.score < 80 ? 'text-yellow-500' : 'text-green-500'}`}>
            {analytics.health.score}
            <span className="text-sm font-normal ml-2">{analytics.health.status}</span>
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
          <div className="text-gray-400 text-sm">Total Tasks</div>
          <div className="text-3xl font-bold text-white mt-1">{analytics.total_tasks}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
          <div className="text-gray-400 text-sm">Overdue Tasks</div>
          <div className="text-3xl font-bold text-red-500 mt-1">{analytics.overdue}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Chart */}
        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
          <h3 className="text-white font-bold mb-4">Task Trends (Last 7 Days)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics.trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none' }} />
                <Legend />
                <Line type="monotone" dataKey="created" stroke="#3B82F6" strokeWidth={2} />
                <Line type="monotone" dataKey="completed" stroke="#10B981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Distribution */}
        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
          <h3 className="text-white font-bold mb-4">Task Status Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Deadlines */}
        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
          <h3 className="text-white font-bold mb-4">Deadlines Overview</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-red-400">Overdue</span>
              <span className="text-white font-medium">{analytics.deadlines.overdue}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-yellow-400">Due Today</span>
              <span className="text-white font-medium">{analytics.deadlines.due_today}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-blue-400">Due Soon (3 days)</span>
              <span className="text-white font-medium">{analytics.deadlines.due_soon}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-green-400">Future</span>
              <span className="text-white font-medium">{analytics.deadlines.future}</span>
            </div>
          </div>
        </div>

        {/* GitHub Analytics */}
        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
          <h3 className="text-white font-bold mb-4">GitHub Activity</h3>
          {gh ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-300">Recent Commits</span>
                <span className="text-white font-medium">{gh.recent_commits}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-300">Open Pull Requests</span>
                <span className="text-white font-medium">{gh.open_prs}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-300">Open Issues</span>
                <span className="text-white font-medium">{gh.open_issues}</span>
              </div>
            </div>
          ) : (
            <div className="text-gray-500 h-full flex items-center justify-center">
              Connect GitHub to unlock repository analytics.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
