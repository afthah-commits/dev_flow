import React, { useEffect, useState } from 'react';
import { apiKeyApi } from '../../lib/apiKeyApi';
import { APIKey } from '../../types/api_key';
import { useOrganization } from '../../contexts/OrganizationContext';
import { Key, Plus, Trash2, ShieldAlert } from 'lucide-react';

export default function ApiKeys() {
  const { currentOrganization } = useOrganization();
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [newKey, setNewKey] = useState<string | null>(null);

  useEffect(() => {
    if (currentOrganization) apiKeyApi.list(currentOrganization.id).then(setKeys);
  }, [currentOrganization]);

  const handleCreate = async () => {
    if (!currentOrganization) return;
    const name = prompt("Key Name:");
    if (!name) return;
    const res = await apiKeyApi.create(currentOrganization.id, { name, scopes: ["projects:read", "tasks:read", "tasks:write"] });
    setNewKey(res.raw_key || null);
    apiKeyApi.list(currentOrganization.id).then(setKeys);
  };

  const handleRevoke = async (id: string) => {
    if (!confirm("Revoke this API Key?")) return;
    await apiKeyApi.revoke(id);
    if (currentOrganization) apiKeyApi.list(currentOrganization.id).then(setKeys);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Key className="w-6 h-6 text-yellow-400" />
            API Keys
          </h1>
          <p className="text-gray-400 mt-1">Manage API keys for the public API.</p>
        </div>
        <button onClick={handleCreate} className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded flex items-center gap-2">
          <Plus className="w-4 h-4" /> Generate Key
        </button>
      </div>

      {newKey && (
        <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 text-yellow-400 mb-2 font-bold">
            <ShieldAlert className="w-5 h-5" /> Please copy your new API key now!
          </div>
          <p className="text-sm text-gray-300 mb-3">You will not be able to see it again.</p>
          <div className="bg-black p-3 rounded font-mono text-green-400 select-all">{newKey}</div>
          <button onClick={() => setNewKey(null)} className="mt-3 text-sm text-gray-400 hover:text-white">Close</button>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-800 text-gray-400">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Prefix</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {keys.map(k => (
              <tr key={k.id}>
                <td className="px-4 py-3 text-white font-medium">{k.name}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-400">{k.key_prefix}...</td>
                <td className="px-4 py-3">
                  {k.revoked_at ? (
                    <span className="text-xs px-2 py-1 rounded-full bg-red-500/10 text-red-400">Revoked</span>
                  ) : (
                    <span className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-400">Active</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  {!k.revoked_at && (
                    <button onClick={() => handleRevoke(k.id)} className="text-red-400 hover:text-red-300">
                      Revoke
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
