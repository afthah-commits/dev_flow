import React, { useEffect, useState } from 'react';
import { useOrganization } from '../../contexts/OrganizationContext';
import { api } from '../../lib/axios';
import { Activity, Users, Folder, CheckSquare, Settings, Key, Zap } from 'lucide-react';

export default function Usage() {
  const { currentOrganization } = useOrganization();
  const [usage, setUsage] = useState<any>(null);

  useEffect(() => {
    if (currentOrganization) {
      api.get(`/organizations/${currentOrganization.id}/usage`).then(res => setUsage(res.data));
    }
  }, [currentOrganization]);

  if (!usage) return <div className="p-8 text-center text-gray-500">Loading usage...</div>;

  const metrics = [
    { label: 'Members', value: usage.members, icon: Users, color: 'text-blue-400' },
    { label: 'Teams', value: usage.teams, icon: Users, color: 'text-indigo-400' },
    { label: 'Projects', value: usage.projects, icon: Folder, color: 'text-yellow-400' },
    { label: 'Tasks', value: usage.tasks, icon: CheckSquare, color: 'text-green-400' },
    { label: 'API Keys', value: usage.api_keys, icon: Key, color: 'text-orange-400' },
    { label: 'Automations', value: usage.automations, icon: Zap, color: 'text-purple-400' },
    { label: 'Webhooks', value: usage.webhooks, icon: Settings, color: 'text-gray-400' },
    { label: 'API Requests (30d)', value: usage.api_requests_monthly, icon: Activity, color: 'text-red-400' }
  ];

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-8">
        <Activity className="w-6 h-6 text-blue-400" />
        Organization Usage
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map(m => (
          <div key={m.label} className="bg-gray-900 border border-gray-800 p-5 rounded-lg flex items-center justify-between">
            <div>
              <div className="text-gray-400 text-sm mb-1">{m.label}</div>
              <div className="text-3xl font-bold text-white">{m.value}</div>
            </div>
            <m.icon className={`w-8 h-8 opacity-20 ${m.color}`} />
          </div>
        ))}
      </div>
    </div>
  );
}
