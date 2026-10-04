import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { deploymentApi } from '../lib/deploymentApi';
import { environmentApi } from '../lib/environmentApi';
import { Deployment } from '../types/deployment';
import { Environment } from '../types/environment';
import { Server, RotateCcw, Clock, AlertCircle, CheckCircle } from 'lucide-react';

export default function Deployments() {
  const { projectId } = useParams<{ projectId: string }>();
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    Promise.all([
      deploymentApi.list(projectId),
      environmentApi.list(projectId)
    ]).then(([deps, envs]) => {
      setDeployments(deps as any);
      setEnvironments(envs as any);
    }).finally(() => setLoading(false));
  }, [projectId]);

  const handleRollback = async (id: string) => {
    if (!confirm('Roll back to this deployment?')) return;
    await deploymentApi.rollback(id);
    if (projectId) {
      const deps = await deploymentApi.list(projectId);
      setDeployments(deps as any);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading deployments...</div>;

  const envMap = new Map(environments.map(e => [e.id, e.name]));

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Server className="w-6 h-6 text-blue-400" />
          Deployments
        </h1>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-800 text-gray-400">
            <tr>
              <th className="px-4 py-3">Environment</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Commit</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3">Time</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {deployments.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No deployments found.</td></tr>
            ) : deployments.map(d => (
              <tr key={d.id} className="hover:bg-gray-800/50">
                <td className="px-4 py-3 font-medium text-white">
                  {d.environment_id ? envMap.get(d.environment_id) || 'Unknown' : 'N/A'}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    d.status === 'SUCCESS' ? 'bg-green-500/10 text-green-400' :
                    d.status === 'FAILED' ? 'bg-red-500/10 text-red-400' :
                    d.status === 'ROLLED_BACK' ? 'bg-yellow-500/10 text-yellow-400' :
                    'bg-blue-500/10 text-blue-400'
                  }`}>
                    {d.status}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono text-xs">{d.commit_sha ? d.commit_sha.substring(0, 7) : '-'}</td>
                <td className="px-4 py-3 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {d.duration_seconds}s
                </td>
                <td className="px-4 py-3 text-gray-400">{new Date(d.created_at).toLocaleString()}</td>
                <td className="px-4 py-3 text-right">
                  {d.status === 'SUCCESS' && (
                    <button 
                      onClick={() => handleRollback(d.id)}
                      className="text-xs flex items-center gap-1 ml-auto text-yellow-400 hover:text-yellow-300 transition-colors"
                    >
                      <RotateCcw className="w-3 h-3" /> Rollback
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
