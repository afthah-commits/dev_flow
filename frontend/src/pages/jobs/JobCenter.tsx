import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useOrganization } from '../../contexts/OrganizationContext';
import { useRealtimeEvent } from '../../hooks/useRealtime';
import { API_BASE } from '../../lib/axios';

interface Job {
  id: string;
  job_type: string;
  status: string;
  attempts: number;
  max_attempts: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export const JobCenter: React.FC = () => {
  const { token } = useAuth();
  const { currentOrganization: currentOrg } = useOrganization();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const fetchJobs = async () => {
    if (!token || !currentOrg) return;
    setLoading(true);
    try {
      const url = new URL(`${API_BASE}/jobs`);
      const res = await fetch(url.toString(), {
        headers: { 'Authorization': `Bearer ${token}`, 'X-Organization-Id': currentOrg.id }
      });
      if (res.ok) setJobs(await res.json());

      const statsRes = await fetch(`${API_BASE}/jobs/stats`, {
        headers: { 'Authorization': `Bearer ${token}`, 'X-Organization-Id': currentOrg.id }
      });
      if (statsRes.ok) setStats(await statsRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [currentOrg, token]);

  useRealtimeEvent("job.updated", fetchJobs);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Job Center</h1>
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-4">
        {['Total', 'QUEUED', 'RUNNING', 'SUCCESS', 'FAILED', 'RETRYING'].map(k => (
          <div key={k} className="bg-gray-800 p-4 rounded text-center">
            <div className="text-2xl font-bold">{stats[k === 'Total' ? 'total' : k] || 0}</div>
            <div className="text-sm text-gray-400">{k}</div>
          </div>
        ))}
      </div>
      
      {loading ? <div>Loading...</div> : (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-800">
              <tr>
                <th className="p-2">ID</th>
                <th className="p-2">Type</th>
                <th className="p-2">Status</th>
                <th className="p-2">Attempts</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map(job => (
                <tr key={job.id} className="border-b border-gray-800">
                  <td className="p-2">{job.id.substring(0,8)}</td>
                  <td className="p-2">{job.job_type}</td>
                  <td className="p-2">{job.status}</td>
                  <td className="p-2">{job.attempts}/{job.max_attempts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
