import React, { useEffect, useState } from 'react';
import { webhookApi } from '../../lib/webhookApi';
import { WebhookEndpoint } from '../../types/webhook';
import { useOrganization } from '../../contexts/OrganizationContext';
import { Globe, Plus, Trash2 } from 'lucide-react';

export default function Webhooks() {
  const { currentOrganization } = useOrganization();
  const [webhooks, setWebhooks] = useState<WebhookEndpoint[]>([]);

  useEffect(() => {
    if (currentOrganization) webhookApi.list(currentOrganization.id).then(setWebhooks);
  }, [currentOrganization]);

  const handleCreate = async () => {
    if (!currentOrganization) return;
    const name = prompt("Webhook Name:");
    const url = prompt("Webhook URL:");
    if (!name || !url) return;
    await webhookApi.create(currentOrganization.id, { name, url, active: true, subscribed_events: ["*"] });
    webhookApi.list(currentOrganization.id).then(setWebhooks);
  };

  const handleDelete = async (id: string) => {
    await webhookApi.remove(id);
    if (currentOrganization) webhookApi.list(currentOrganization.id).then(setWebhooks);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Globe className="w-6 h-6 text-green-400" />
            Webhooks
          </h1>
          <p className="text-gray-400 mt-1">Receive real-time HTTP events.</p>
        </div>
        <button onClick={handleCreate} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Webhook
        </button>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-800 text-gray-400">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">URL</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {webhooks.map(w => (
              <tr key={w.id}>
                <td className="px-4 py-3 text-white font-medium">{w.name}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-400">{w.url}</td>
                <td className="px-4 py-3">
                  <span className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-400">Active</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => handleDelete(w.id)} className="text-red-400 hover:text-red-300">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
