import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { workflowApi, StudioGraph } from '../lib/workflowApi';
import { useOrganization } from '../contexts/OrganizationContext';

interface WorkflowListItem {
  id: string;
  name: string;
  description?: string | null;
  entity_type: string;
  is_active: boolean;
  states: { id: string; name: string; key: string }[];
  transitions: { id: string; name: string }[];
}

export const Workflows: React.FC = () => {
  const { currentOrganization } = useOrganization();
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await workflowApi.list();
      setWorkflows(data as WorkflowListItem[]);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load workflows');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (currentOrganization) load();
  }, [currentOrganization, load]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const wf = await workflowApi.create({ name: newName.trim(), entity_type: 'TASK' });
      setNewName('');
      navigate(`/workflows/${wf.id}/studio`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to create workflow');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Workflows</h1>
          <p className="text-sm text-gray-400">Visual business-process studio — design, validate, simulate, publish.</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded border border-red-800 bg-red-900/30 text-red-200 px-4 py-3 text-sm">{error}</div>
      )}

      <div className="mb-6 flex gap-2">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          placeholder="New workflow name…"
          className="flex-1 max-w-sm rounded border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none"
        />
        <button
          onClick={handleCreate}
          disabled={creating || !newName.trim()}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {creating ? 'Creating…' : 'New Workflow'}
        </button>
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm">Loading workflows…</div>
      ) : workflows.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-700 p-10 text-center text-gray-400">
          No workflows yet. Create your first one above.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workflows.map((wf) => (
            <Link
              key={wf.id}
              to={`/workflows/${wf.id}/studio`}
              className="block rounded-lg border border-gray-800 bg-gray-900 p-4 hover:border-blue-600 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-white truncate">{wf.name}</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full ${wf.is_active ? 'bg-green-900/50 text-green-300' : 'bg-gray-800 text-gray-400'}`}>
                  {wf.is_active ? 'Active' : 'Draft'}
                </span>
              </div>
              <p className="text-xs text-gray-400 mb-3 line-clamp-2">{wf.description || 'No description'}</p>
              <div className="flex gap-3 text-xs text-gray-500">
                <span>{wf.states?.length ?? 0} states</span>
                <span>{wf.transitions?.length ?? 0} transitions</span>
                <span className="uppercase">{wf.entity_type}</span>
              </div>
              <div className="mt-3 text-xs text-blue-400">Open Studio →</div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default Workflows;
