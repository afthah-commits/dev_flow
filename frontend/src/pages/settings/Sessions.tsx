import React, { useEffect, useState } from 'react';
import { api } from '../../lib/axios';

export default function Sessions() {
  const [sessions, setSessions] = useState<any[]>([]);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const res = await api.get('/security/sessions');
      setSessions(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRevoke = async (id: string) => {
    try {
      await api.delete(`/security/sessions/${id}`);
      loadSessions();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRevokeOthers = async () => {
    try {
      await api.post('/security/sessions/revoke-others');
      loadSessions();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Active Sessions</h1>
        <button 
          onClick={handleRevokeOthers}
          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm font-medium"
        >
          Revoke All Other Sessions
        </button>
      </div>
      
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {sessions.map(session => (
            <li key={session.id} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <p className="text-sm font-medium text-gray-900">
                    {session.device_name || 'Unknown Device'} - {session.browser || 'Unknown Browser'}
                  </p>
                  <p className="text-sm text-gray-500">
                    IP: {session.ip_address || 'Unknown'} | Last active: {new Date(session.last_seen_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  {!session.is_current ? (
                    <button 
                      onClick={() => handleRevoke(session.id)}
                      className="text-red-600 hover:text-red-900 text-sm font-medium"
                    >
                      Revoke
                    </button>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Current Session
                    </span>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}


