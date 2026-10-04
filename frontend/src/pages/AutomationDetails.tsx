import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { automationApi } from '../lib/automationApi';
import { useOrganization } from '../contexts/OrganizationContext';
import { Automation } from '../types/automation';
import { Save, ArrowLeft, Wand2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function AutomationDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentOrganization } = useOrganization();
  
  const [automation, setAutomation] = useState<Partial<Automation>>({
    name: 'New Automation',
    description: '',
    enabled: true,
    trigger_type: 'TASK_STATUS_CHANGED',
    conditions: { logical_operator: 'ALL', conditions: [] },
    actions: []
  });
  const [loading, setLoading] = useState(id !== 'new');
  const [aiPrompt, setAiPrompt] = useState('');

  useEffect(() => {
    if (id === 'new' || !id) return;
    automationApi.get(id).then(setAutomation).finally(() => setLoading(false));
  }, [id]);

  const handleSave = async () => {
    if (!currentOrganization) return;
    try {
      if (id === 'new') {
        const res = await automationApi.create(currentOrganization.id, automation);
        navigate(`/automations/${res.id}`);
      } else {
        await automationApi.update(id as string, automation);
        alert('Saved!');
      }
    } catch (e) {
      console.error(e);
      alert('Failed to save');
    }
  };

  const handleGenerate = async () => {
    if (!aiPrompt) return;
    try {
      const generated = await automationApi.generateAI(aiPrompt);
      setAutomation(prev => ({ ...prev, ...generated }));
      setAiPrompt('');
    } catch (e) {
      console.error(e);
      alert('AI Generation failed');
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-400">Loading...</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/automations" className="text-gray-400 hover:text-white">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <input 
            value={automation.name} 
            onChange={e => setAutomation({...automation, name: e.target.value})}
            className="bg-transparent text-2xl font-bold text-white border-none focus:outline-none w-full"
            placeholder="Automation Name"
          />
        </div>
        <button onClick={handleSave} className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded font-medium flex items-center gap-2">
          <Save className="w-4 h-4" /> Save
        </button>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex gap-2">
        <input 
          type="text"
          value={aiPrompt}
          onChange={e => setAiPrompt(e.target.value)}
          placeholder="Describe your workflow to AI..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
        />
        <button onClick={handleGenerate} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white font-medium flex items-center gap-2">
          <Wand2 className="w-4 h-4" /> Generate
        </button>
      </div>

      <div className="space-y-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <h3 className="text-lg font-medium text-white mb-4">1. Trigger</h3>
          <select 
            value={automation.trigger_type}
            onChange={e => setAutomation({...automation, trigger_type: e.target.value})}
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
          >
            <option value="TASK_CREATED">Task Created</option>
            <option value="TASK_UPDATED">Task Updated</option>
            <option value="TASK_STATUS_CHANGED">Task Status Changed</option>
            <option value="DEPLOYMENT_FAILED">Deployment Failed</option>
            <option value="PULL_REQUEST_MERGED">Pull Request Merged</option>
          </select>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <h3 className="text-lg font-medium text-white mb-4">2. Conditions</h3>
          <p className="text-sm text-gray-400 mb-2">JSON Configuration for now (Visual builder coming soon):</p>
          <textarea 
            value={JSON.stringify(automation.conditions, null, 2)}
            onChange={e => {
              try {
                setAutomation({...automation, conditions: JSON.parse(e.target.value)})
              } catch(err){}
            }}
            className="w-full h-32 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white font-mono text-sm"
          />
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <h3 className="text-lg font-medium text-white mb-4">3. Actions</h3>
          <p className="text-sm text-gray-400 mb-2">JSON Actions:</p>
          <textarea 
            value={JSON.stringify(automation.actions, null, 2)}
            onChange={e => {
              try {
                setAutomation({...automation, actions: JSON.parse(e.target.value)})
              } catch(err){}
            }}
            className="w-full h-32 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white font-mono text-sm"
          />
        </div>
      </div>
    </div>
  );
}
