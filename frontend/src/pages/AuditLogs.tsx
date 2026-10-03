import React, { useState, useEffect } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { api } from '../lib/axios';

export function AuditLogs() {
  const { currentOrganization } = useOrganization();
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const [filterType, setFilterType] = useState('');
  const [filterEntity, setFilterEntity] = useState('');

  useEffect(() => {
    if (currentOrganization) {
      loadEvents();
    }
  }, [currentOrganization, page, filterType, filterEntity]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        organization_id: currentOrganization!.id,
        page: page.toString(),
        page_size: '50'
      });
      if (filterType) params.append('event_type', filterType);
      if (filterEntity) params.append('entity_type', filterEntity);

      const res = await api.get(`/audit/events?${params.toString()}`);
      setEvents(res.data.items);
      setTotal(res.data.total);
      setError(null);
    } catch (e: any) {
      if (e.response?.status === 403) {
        setError("You do not have permission to view organization audit logs.");
      } else {
        setError("Failed to load audit logs.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const params = new URLSearchParams({ organization_id: currentOrganization!.id });
      const res = await api.get(`/audit/events/export?${params.toString()}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_export_${currentOrganization!.id}.csv`);
      document.body.appendChild(link);
      link.click();
    } catch (e) {
      alert("Failed to export audit logs");
    }
  };

  if (!currentOrganization) return null;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Audit Logs</h1>
          <p className="text-gray-400">View all activity across your organization.</p>
        </div>
        <button 
          onClick={handleExport}
          className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded transition-colors text-sm font-medium"
        >
          Export CSV
        </button>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <div className="flex gap-4 mb-6">
          <input 
            type="text" 
            placeholder="Filter by Event Type (e.g. TASK_CREATED)" 
            className="bg-gray-800 text-white text-sm rounded border border-gray-700 p-2 outline-none w-64"
            value={filterType}
            onChange={e => { setFilterType(e.target.value); setPage(1); }}
          />
          <input 
            type="text" 
            placeholder="Filter by Entity Type (e.g. TASK)" 
            className="bg-gray-800 text-white text-sm rounded border border-gray-700 p-2 outline-none w-64"
            value={filterEntity}
            onChange={e => { setFilterEntity(e.target.value); setPage(1); }}
          />
        </div>

        {error ? (
          <div className="text-red-400 py-8 text-center">{error}</div>
        ) : loading ? (
          <div className="text-gray-400 py-8 text-center animate-pulse">Loading audit logs...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-gray-800 text-xs uppercase text-gray-400">
                <tr>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Event Type</th>
                  <th className="px-4 py-3">Entity Type</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Details</th>
                </tr>
              </thead>
              <tbody>
                {events.length === 0 ? (
                  <tr><td colSpan={5} className="text-center py-8 text-gray-500">No events found.</td></tr>
                ) : (
                  events.map(e => (
                    <tr key={e.id} className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
                      <td className="px-4 py-3 whitespace-nowrap">{new Date(e.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3 font-medium text-blue-400">{e.event_type}</td>
                      <td className="px-4 py-3">{e.entity_type}</td>
                      <td className="px-4 py-3 font-mono text-xs">{e.actor_user_id || 'System'}</td>
                      <td className="px-4 py-3 max-w-xs truncate text-xs text-gray-500">
                        {JSON.stringify(e.metadata)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
            
            {total > 50 && (
              <div className="mt-4 flex justify-between items-center text-sm">
                <span className="text-gray-500">Showing {events.length} of {total}</span>
                <div className="flex gap-2">
                  <button 
                    disabled={page === 1} 
                    onClick={() => setPage(p => p - 1)}
                    className="px-3 py-1 bg-gray-800 rounded disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button 
                    disabled={events.length < 50} 
                    onClick={() => setPage(p => p + 1)}
                    className="px-3 py-1 bg-gray-800 rounded disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
