import React, { useState } from 'react';
import { api } from '../../lib/axios';

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
