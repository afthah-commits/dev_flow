import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { pipelineApi } from '../lib/pipelineApi';
import { PipelineRun } from '../types/pipeline';
import { Play, CheckCircle2, XCircle, Clock } from 'lucide-react';

export default function PipelineRuns() {
  const { projectId } = useParams<{ projectId: string }>();
  const [pipelines, setPipelines] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    pipelineApi.list(projectId)
      .then(setPipelines)
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div className="p-8 text-center text-gray-500">Loading pipelines...</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Play className="w-6 h-6 text-emerald-400" />
          Pipeline Runs
        </h1>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-800 text-gray-400">
            <tr>
              <th className="px-4 py-3">Workflow</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Branch</th>
              <th className="px-4 py-3">Commit</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {pipelines.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No pipelines found.</td></tr>
            ) : pipelines.map(p => (
              <tr key={p.id} className="hover:bg-gray-800/50">
                <td className="px-4 py-3 font-medium text-white">{p.workflow_name || 'CI'}</td>
                <td className="px-4 py-3 flex items-center gap-2">
                  {p.status === 'SUCCESS' ? <CheckCircle2 className="w-4 h-4 text-green-400" /> :
                   p.status === 'FAILED' ? <XCircle className="w-4 h-4 text-red-400" /> :
                   <Clock className="w-4 h-4 text-blue-400" />}
                  <span className={
                    p.status === 'SUCCESS' ? 'text-green-400' :
                    p.status === 'FAILED' ? 'text-red-400' : 'text-blue-400'
                  }>{p.status}</span>
                </td>
                <td className="px-4 py-3">{p.branch || '-'}</td>
                <td className="px-4 py-3 font-mono text-xs">{p.commit_sha ? p.commit_sha.substring(0, 7) : '-'}</td>
                <td className="px-4 py-3">{p.duration_seconds}s</td>
                <td className="px-4 py-3 text-gray-400">{new Date(p.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
