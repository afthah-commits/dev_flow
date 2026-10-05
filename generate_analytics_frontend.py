import os

PAGES = {
    "frontend/src/pages/analytics/ExecutiveDashboard.tsx": """import React, { useEffect, useState } from 'react';
import api from '../../lib/api';

export default function ExecutiveDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/analytics/executive')
      .then((res: any) => setData(res.data))
      .catch((err: any) => setError(err.response?.data?.detail || 'Failed to load executive analytics'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Executive Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
        <div className="bg-white p-4 rounded shadow">
          <p className="text-gray-500 text-sm">Active Projects</p>
          <p className="text-3xl font-bold">{data?.active_projects}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-gray-500 text-sm">Completed Projects</p>
          <p className="text-3xl font-bold">{data?.completed_projects}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-gray-500 text-sm">Open Tasks</p>
          <p className="text-3xl font-bold">{data?.open_tasks}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-gray-500 text-sm">Deployment Success</p>
          <p className="text-3xl font-bold">{data?.deployment_success_rate}%</p>
        </div>
      </div>
    </div>
  );
}
""",
    "frontend/src/pages/analytics/ProjectAnalytics.tsx": """import React, { useState } from 'react';
import api from '../../lib/api';

export default function ProjectAnalytics() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [projectId, setProjectId] = useState('');

  const loadData = () => {
    if (!projectId) return;
    setLoading(true);
    api.get(`/analytics/projects/${projectId}`)
      .then((res: any) => setData(res.data))
      .catch((err: any) => setError(err.response?.data?.detail || 'Failed to load project analytics'))
      .finally(() => setLoading(false));
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Project Analytics</h1>
      <div className="mb-4 flex gap-4">
        <input 
          type="text" 
          placeholder="Project ID" 
          className="border p-2 rounded"
          value={projectId} 
          onChange={(e: any) => setProjectId(e.target.value)} 
        />
        <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={loadData}>Load</button>
      </div>
      {loading && <div>Loading...</div>}
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {data && (
        <div className="bg-white p-4 rounded shadow max-w-sm">
          <h2 className="text-lg font-bold mb-2">Task Completion</h2>
          <p className="text-3xl font-bold">{data.task_completion?.toFixed(1)}%</p>
          <p className="text-gray-600 mt-2">Total Tasks: {data.total_tasks}</p>
          <p className="text-gray-600">Overdue: {data.overdue_tasks}</p>
        </div>
      )}
    </div>
  );
}
""",
    "frontend/src/pages/analytics/TeamAnalytics.tsx": """import React, { useState } from 'react';
import api from '../../lib/api';

export default function TeamAnalytics() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [teamId, setTeamId] = useState('');

  const loadData = () => {
    if (!teamId) return;
    setLoading(true);
    api.get(`/analytics/teams/${teamId}`)
      .then((res: any) => setData(res.data))
      .catch((err: any) => setError(err.response?.data?.detail || 'Failed to load team analytics'))
      .finally(() => setLoading(false));
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Team Analytics</h1>
      <div className="mb-4 flex gap-4">
        <input 
          type="text" 
          placeholder="Team ID" 
          className="border p-2 rounded"
          value={teamId} 
          onChange={(e: any) => setTeamId(e.target.value)} 
        />
        <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={loadData}>Load</button>
      </div>
      {loading && <div>Loading...</div>}
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {data && (
        <div className="bg-white p-4 rounded shadow max-w-sm">
          <h2 className="text-lg font-bold mb-2">Team Performance</h2>
          <p className="text-gray-600 mt-2">Members: {data.member_count}</p>
          <p className="text-gray-600">Assigned Tasks: {data.assigned_tasks}</p>
          <p className="text-gray-600">Completed Tasks: {data.completed_tasks}</p>
        </div>
      )}
    </div>
  );
}
""",
    "frontend/src/pages/analytics/SprintAnalytics.tsx": """import React, { useState } from 'react';
import api from '../../lib/api';

export default function SprintAnalytics() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sprintId, setSprintId] = useState('');

  const loadData = () => {
    if (!sprintId) return;
    setLoading(true);
    api.get(`/analytics/sprints/${sprintId}`)
      .then((res: any) => setData(res.data))
      .catch((err: any) => setError(err.response?.data?.detail || 'Failed to load sprint analytics'))
      .finally(() => setLoading(false));
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Sprint Analytics</h1>
      <div className="mb-4 flex gap-4">
        <input 
          type="text" 
          placeholder="Sprint ID" 
          className="border p-2 rounded"
          value={sprintId} 
          onChange={(e: any) => setSprintId(e.target.value)} 
        />
        <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={loadData}>Load</button>
      </div>
      {loading && <div>Loading...</div>}
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {data && (
        <div className="bg-white p-4 rounded shadow max-w-sm">
          <h2 className="text-lg font-bold mb-2">Sprint Velocity</h2>
          <p className="text-3xl font-bold">{data.velocity}</p>
          <p className="text-gray-600 mt-2">Planned Points: {data.planned_points}</p>
          <p className="text-gray-600">Remaining Points: {data.remaining_points}</p>
        </div>
      )}
    </div>
  );
}
"""
}

for filepath, content in PAGES.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"Created {filepath}")
