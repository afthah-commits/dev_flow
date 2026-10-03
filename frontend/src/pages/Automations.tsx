import React, { useEffect, useState } from 'react';
import { automationApi } from '../lib/automationApi';
import { Automation } from '../types/automation';
import { useAuth } from '../hooks/useAuth';
import { Play, Plus, Settings, AlertCircle, Edit2, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Automations() {
  const { currentOrganization } = useAuth();
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAutomations = async () => {
    if (!currentOrganization) return;
    try {
      const data = await automationApi.list(currentOrganization.id);
      setAutomations(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAutomations();
  }, [currentOrganization]);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this automation?')) return;
    await automationApi.remove(id);
    await fetchAutomations();
  };

  const handleToggle = async (id: string, current: boolean) => {
    await automationApi.update(id, { enabled: !current });
    await fetchAutomations();
  };

  if (loading) return <div className="p-8 text-center text-gray-400">Loading automations...</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Settings className="w-6 h-6 text-purple-400" />
            Automations & Workflows
          </h1>
          <p className="text-gray-400 mt-1">Automate your organization's processes.</p>
        </div>
        <Link 
          to="/automations/new" 
          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded font-medium flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> Create Automation
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {automations.map(a => (
          <div key={a.id} className="bg-gray-900 border border-gray-800 rounded-lg p-5 flex flex-col">
            <div className="flex justify-between items-start mb-3">
              <h3 className="text-lg font-medium text-white">{a.name}</h3>
              <button 
                onClick={() => handleToggle(a.id, a.enabled)}
                className={\w-10 h-5 rounded-full transition-colors relative \\}
              >
                <div className={\w-3 h-3 bg-white rounded-full absolute top-1 transition-all \\} />
              </button>
            </div>
            <p className="text-sm text-gray-400 flex-1">{a.description || 'No description'}</p>
            <div className="mt-4 pt-4 border-t border-gray-800 flex items-center justify-between">
              <span className="text-xs text-purple-400 bg-purple-500/10 px-2 py-1 rounded">
                {a.trigger_type}
              </span>
              <div className="flex items-center gap-2">
                <Link to={\/automations/\\} className="p-1 text-gray-400 hover:text-white">
                  <Edit2 className="w-4 h-4" />
                </Link>
                <button onClick={() => handleDelete(a.id)} className="p-1 text-gray-400 hover:text-red-400">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
        {automations.length === 0 && (
          <div className="col-span-full p-8 text-center bg-gray-900 border border-gray-800 rounded-lg text-gray-400">
            No automations found. Create your first workflow!
          </div>
        )}
      </div>
    </div>
  );
}
