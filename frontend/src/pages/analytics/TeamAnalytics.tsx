import React, { useState } from 'react';
import { api } from '../../lib/axios';

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
