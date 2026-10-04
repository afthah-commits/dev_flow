import React, { useEffect, useState } from 'react';
import { useOrganization } from '../../contexts/OrganizationContext';
import { integrationHubApi } from '../../lib/integrationHubApi';
import { Integration, ApiUsage } from '../../types/integrationHub';

export default function DeveloperSettings() {
  const { currentOrganization } = useOrganization();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [usage, setUsage] = useState<ApiUsage | null>(null);

  useEffect(() => {
    if (currentOrganization) {
      loadIntegrations();
      loadUsage();
    }
  }, [currentOrganization]);

  const loadIntegrations = async () => {
    if (!currentOrganization) return;
    try {
      const data = await integrationHubApi.getIntegrations(currentOrganization.id);
      setIntegrations(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadUsage = async () => {
    if (!currentOrganization) return;
    try {
      const data = await integrationHubApi.getApiUsage(currentOrganization.id);
      setUsage(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleTest = async (id: string) => {
    if (!currentOrganization) return;
    try {
      await integrationHubApi.testIntegration(currentOrganization.id, id);
      alert("Test sent successfully.");
    } catch (e) {
      console.error(e);
    }
  };

  const toggleEnabled = async (id: string, currentlyEnabled: boolean) => {
    if (!currentOrganization) return;
    try {
      if (currentlyEnabled) {
        await integrationHubApi.disableIntegration(currentOrganization.id, id);
      } else {
        await integrationHubApi.enableIntegration(currentOrganization.id, id);
      }
      loadIntegrations();
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateMock = async (provider: string) => {
    if (!currentOrganization) return;
    try {
      await integrationHubApi.createIntegration(currentOrganization.id, {
        provider,
        name: `Mock ${provider}`,
        status: 'ACTIVE',
        enabled: true,
        configuration: {}
      });
      loadIntegrations();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Developer & Integration Hub</h1>
      
      {usage && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Total API Requests</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">{usage.total_requests}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Webhook Deliveries</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">{usage.webhook_deliveries}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Failed Deliveries</h3>
            <p className="mt-2 text-3xl font-semibold text-red-600">{usage.failed_deliveries}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Integration Events</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">{usage.integration_events}</p>
          </div>
        </div>
      )}

      <div className="mb-6 flex space-x-4">
        <button onClick={() => handleCreateMock('SLACK')} className="bg-white border border-gray-300 shadow-sm px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
          Add Mock Slack
        </button>
        <button onClick={() => handleCreateMock('GOOGLE_CALENDAR')} className="bg-white border border-gray-300 shadow-sm px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
          Add Mock Google Calendar
        </button>
        <button onClick={() => handleCreateMock('EMAIL')} className="bg-white border border-gray-300 shadow-sm px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
          Add Mock Email
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {integrations.map(integration => (
            <li key={integration.id} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <p className="text-sm font-medium text-indigo-600 truncate">{integration.name}</p>
                  <p className="text-sm text-gray-500">Provider: {integration.provider}</p>
                </div>
                <div className="flex space-x-4 items-center">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${integration.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {integration.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                  <button onClick={() => handleTest(integration.id)} className="text-indigo-600 hover:text-indigo-900 text-sm font-medium">Test</button>
                  <button onClick={() => toggleEnabled(integration.id, integration.enabled)} className="text-gray-600 hover:text-gray-900 text-sm font-medium">
                    {integration.enabled ? 'Disable' : 'Enable'}
                  </button>
                </div>
              </div>
            </li>
          ))}
          {integrations.length === 0 && (
            <li className="px-4 py-8 text-center text-gray-500">No integrations connected.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
