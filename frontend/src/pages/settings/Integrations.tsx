import React, { useEffect, useState } from 'react';
import { integrationApi } from '../../lib/integrationApi';
import { Integration } from '../../types/integration';
import { useOrganization } from '../../contexts/OrganizationContext';
import { Settings, Link, Calendar, Mail, MessageSquare } from 'lucide-react';

export default function Integrations() {
  const { currentOrganization } = useOrganization();
  const [integrations, setIntegrations] = useState<Integration[]>([]);

  useEffect(() => {
    if (currentOrganization) {
      integrationApi.list(currentOrganization.id).then(setIntegrations);
    }
  }, [currentOrganization]);

  const handleConnectSlack = async () => {
    if (!currentOrganization) return;
    await integrationApi.create(currentOrganization.id, {
      provider: 'slack',
      name: 'Slack Workspace',
      status: 'ACTIVE',
      configuration: {}
    });
    integrationApi.list(currentOrganization.id).then(setIntegrations);
  };

  const handleDisconnect = async (id: string) => {
    await integrationApi.remove(id);
    if (currentOrganization) integrationApi.list(currentOrganization.id).then(setIntegrations);
  };

  const slackConnected = integrations.find(i => i.provider === 'slack');

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Link className="w-6 h-6 text-blue-400" />
            Integrations
          </h1>
          <p className="text-gray-400 mt-1">Connect DevFlow with your external tools.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Slack Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-gray-800 p-2 rounded-lg">
              <MessageSquare className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-white">Slack</h3>
              <p className="text-sm text-gray-400">Team notifications</p>
            </div>
          </div>
          <p className="text-sm text-gray-400 mb-6 flex-1">Receive automated task and sprint updates directly in your Slack channels.</p>
          {slackConnected ? (
            <div className="flex items-center justify-between">
              <span className="text-sm text-green-400 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-400 rounded-full"></span> Connected
              </span>
              <button onClick={() => handleDisconnect(slackConnected.id)} className="text-sm text-red-400 hover:text-red-300">Disconnect</button>
            </div>
          ) : (
            <button onClick={handleConnectSlack} className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium">Connect Slack</button>
          )}
        </div>
      </div>
    </div>
  );
}
