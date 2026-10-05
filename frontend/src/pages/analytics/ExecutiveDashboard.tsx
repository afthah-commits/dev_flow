import React, { useEffect, useState } from 'react';
import { api } from '../../lib/axios';

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
