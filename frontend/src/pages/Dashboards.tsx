import React, { useEffect, useState } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { reportApi } from '../lib/reportApi';
import { Dashboard } from '../types/report';

export default function Dashboards() {
  const { currentOrganization } = useOrganization();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentOrganization) {
      loadDashboards();
    }
  }, [currentOrganization]);

  const loadDashboards = async () => {
    if (!currentOrganization) return;
    try {
      const data = await reportApi.getDashboards(currentOrganization.id);
      setDashboards(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!currentOrganization) return;
    try {
      await reportApi.createDashboard(currentOrganization.id, {
        name: 'New Dashboard',
        is_default: dashboards.length === 0
      });
      loadDashboards();
    } catch (error) {
      console.error(error);
    }
  };

  if (loading) return <div className="p-8">Loading dashboards...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Custom Dashboards</h1>
        <button 
          onClick={handleCreate}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
        >
          Create Dashboard
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {dashboards.map(dash => (
          <div key={dash.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">{dash.name}</h3>
            {dash.description && <p className="text-gray-500 mt-1">{dash.description}</p>}
            <div className="mt-4 text-sm text-gray-500">
              {dash.widgets?.length || 0} Widgets
            </div>
            {dash.is_default && (
              <span className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Default Dashboard
              </span>
            )}
            <div className="mt-4">
              <button className="text-indigo-600 hover:text-indigo-900 font-medium text-sm">
                View Dashboard &rarr;
              </button>
            </div>
          </div>
        ))}
        
        {dashboards.length === 0 && (
          <div className="col-span-3 text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <p className="text-gray-500">No dashboards created yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
