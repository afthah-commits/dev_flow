import React, { useEffect, useState } from 'react';
import { api } from '../lib/axios';
import { Release } from '../types/release';
import { Rocket, Server, Activity, ShieldCheck, ArrowRight, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ReleaseOperations() {
  const [releases, setReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // A more advanced app would have a cross-project releases endpoint, 
    // but for now we fetch all projects and their releases, or use a simplified approach
    // We'll mock it or fetch an operations specific endpoint
    api.get('/projects').then(async (res) => {
      const allReleases: Release[] = [];
      for (const p of res.data) {
        try {
          const rRes = await api.get(`/projects/${p.id}/releases`);
          allReleases.push(...rRes.data);
        } catch (e) {}
      }
      setReleases(allReleases.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-500">Loading operations...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Server className="w-6 h-6 text-blue-500" />
            Release Operations
          </h1>
          <p className="text-gray-400 mt-1">Cross-project deployment pipeline and approvals.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Ready for Review', value: releases.filter(r => r.status === 'READY').length, icon: ShieldCheck, color: 'text-yellow-400' },
          { label: 'Approved', value: releases.filter(r => r.status === 'APPROVED').length, icon: Activity, color: 'text-green-400' },
          { label: 'Deploying', value: releases.filter(r => r.status === 'DEPLOYING').length, icon: Rocket, color: 'text-blue-400' },
          { label: 'Failed', value: releases.filter(r => r.status === 'FAILED').length, icon: ArrowLeft, color: 'text-red-400' },
        ].map(stat => (
          <div key={stat.label} className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-400">{stat.label}</span>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div className="text-2xl font-bold text-white">{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-300">
            <thead className="bg-gray-800 text-gray-400 uppercase text-xs">
              <tr>
                <th className="px-6 py-4 font-medium">Release</th>
                <th className="px-6 py-4 font-medium">Target</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Created</th>
                <th className="px-6 py-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {releases.map((r) => (
                <tr key={r.id} className="hover:bg-gray-800/50">
                  <td className="px-6 py-4 font-medium text-white">
                    {r.name}
                    <div className="text-xs text-gray-500 font-mono mt-1">{r.version}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 bg-gray-800 rounded text-xs">
                      {r.target_environment || 'Unspecified'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium border ${
                      r.status === 'DEPLOYED' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                      r.status === 'READY' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                      r.status === 'APPROVED' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                      r.status === 'FAILED' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                      'bg-gray-800 text-gray-400 border-gray-700'
                    }`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-400 text-xs">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <Link
                      to={`/projects/${r.project_id}/releases/${r.id}`}
                      className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
                    >
                      View Details
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
