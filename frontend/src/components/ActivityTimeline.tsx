import React, { useState, useEffect } from 'react';
import { api } from '../lib/axios';
import { useOrganization } from '../contexts/OrganizationContext';

export function ActivityTimeline({ 
  projectId, 
  taskId, 
  sprintId 
}: { 
  projectId?: string, 
  taskId?: string, 
  sprintId?: string 
}) {
  const { currentOrganization } = useOrganization();
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentOrganization) {
      loadEvents();
    }
  }, [currentOrganization, projectId, taskId, sprintId]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        organization_id: currentOrganization!.id,
        page_size: '20'
      });
      if (projectId) params.append('project_id', projectId);
      // Backend doesn't support task_id/sprint_id filtering explicitly in the router unless we pass entity_type and entity_id
      if (taskId) {
        params.append('entity_type', 'TASK');
        params.append('entity_id', taskId);
      }
      if (sprintId) {
        params.append('entity_type', 'SPRINT');
        params.append('entity_id', sprintId);
      }
      
      const res = await api.get(`/audit/events?${params.toString()}`);
      setEvents(res.data.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-gray-400 text-sm animate-pulse">Loading activity...</div>;
  if (events.length === 0) return <div className="text-gray-500 text-sm">No activity yet.</div>;

  return (
    <div className="space-y-4">
      {events.map((e, idx) => (
        <div key={e.id} className="flex gap-3 text-sm">
          <div className="flex flex-col items-center">
            <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-xs font-medium border border-gray-700">
              {e.actor_user_id ? 'U' : 'S'}
            </div>
            {idx < events.length - 1 && <div className="w-px h-full bg-gray-800 my-1 flex-1"></div>}
          </div>
          <div className="pb-4 flex-1">
            <p className="text-gray-300">
              <span className="font-medium text-white">{e.actor_user_id || 'System'}</span> 
              {' '}
              <span className="text-gray-400">{e.event_type.toLowerCase().replace(/_/g, ' ')}</span>
            </p>
            <p className="text-xs text-gray-500 mt-1">{new Date(e.created_at).toLocaleString()}</p>
            {e.metadata?.changes && (
              <div className="mt-2 space-y-1">
                {e.metadata.changes.map((c: any, i: number) => (
                  <div key={i} className="text-xs bg-gray-900 border border-gray-800 p-2 rounded">
                    <span className="font-medium text-gray-400">{c.field}:</span>{' '}
                    <span className="line-through text-gray-500">{String(c.old)}</span> &rarr; <span className="text-blue-400">{String(c.new)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
