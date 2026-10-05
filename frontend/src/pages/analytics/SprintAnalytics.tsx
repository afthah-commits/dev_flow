import React, { useState } from 'react';
import { api } from '../../lib/axios';

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
