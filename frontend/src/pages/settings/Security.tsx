import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../lib/axios';
import { Shield, Key, Smartphone, Monitor, Clock, LogOut } from 'lucide-react';

export default function Security() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [mfaData, setMfaData] = useState<any>(null);
  const [mfaCode, setMfaCode] = useState('');

  useEffect(() => {
    api.get('/security/sessions').then(res => setSessions(res.data));
    api.get('/security/login-history').then(res => setHistory(res.data));
  }, []);

  const revokeSession = async (id: string) => {
    if(!confirm("Revoke this session?")) return;
    await api.delete(`/security/sessions/${id}`);
    setSessions(sessions.filter(s => s.id !== id));
  };

  const setupMFA = async () => {
    const res = await api.post('/security/mfa/setup');
    setMfaData(res.data);
  };

  const verifyMFA = async () => {
    const res = await api.post(`/security/mfa/verify?code=${mfaCode}`);
    alert(res.data.message);
    setMfaData(null);
    window.location.reload();
  };

  const disableMFA = async () => {
    const code = prompt("Enter MFA code to disable:");
    if (!code) return;
    await api.post(`/security/mfa/disable?code=${code}`);
    alert("MFA Disabled");
    window.location.reload();
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Shield className="w-6 h-6 text-purple-400" />
        Security Center
      </h1>

      <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg">
        <h2 className="text-xl font-medium text-white mb-4 flex items-center gap-2">
          <Smartphone className="w-5 h-5 text-blue-400" />
          Two-Factor Authentication (MFA)
        </h2>
        {user?.mfa_enabled ? (
          <div>
            <p className="text-green-400 mb-4">MFA is currently enabled.</p>
            <button onClick={disableMFA} className="bg-red-500/20 text-red-400 px-4 py-2 rounded hover:bg-red-500/30">
              Disable MFA
            </button>
          </div>
        ) : mfaData ? (
          <div className="space-y-4">
            <p className="text-gray-300">Scan this code with your authenticator app (MOCK):</p>
            <div className="bg-gray-800 p-4 font-mono text-center text-sm">{mfaData.uri}</div>
            <p className="text-gray-300">Secret: {mfaData.secret}</p>
            <div className="flex gap-2">
              <input type="text" placeholder="Enter 6-digit code (e.g. 123456)" className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white" value={mfaCode} onChange={e => setMfaCode(e.target.value)} />
              <button onClick={verifyMFA} className="bg-blue-600 text-white px-4 py-2 rounded">Verify & Enable</button>
            </div>
          </div>
        ) : (
          <div>
            <p className="text-gray-400 mb-4">Protect your account with an extra layer of security.</p>
            <button onClick={setupMFA} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              Setup MFA
            </button>
          </div>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg">
        <h2 className="text-xl font-medium text-white mb-4 flex items-center gap-2">
          <Monitor className="w-5 h-5 text-green-400" />
          Active Sessions
        </h2>
        <div className="space-y-3">
          {sessions.map(s => (
            <div key={s.id} className="flex justify-between items-center bg-gray-800 p-3 rounded">
              <div>
                <div className="text-white font-medium">{s.device_name || 'Unknown Device'}</div>
                <div className="text-xs text-gray-400">{s.browser} on {s.operating_system} • {s.ip_address}</div>
                <div className="text-xs text-gray-500 mt-1">Last seen: {new Date(s.last_seen_at).toLocaleString()}</div>
              </div>
              <button onClick={() => revokeSession(s.id)} className="text-red-400 hover:text-red-300 p-2" title="Revoke Session">
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 p-5 rounded-lg">
        <h2 className="text-xl font-medium text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-yellow-400" />
          Login History
        </h2>
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-800 text-gray-400">
            <tr>
              <th className="p-3">Time</th>
              <th className="p-3">Status</th>
              <th className="p-3">IP / Device</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {history.map(h => (
              <tr key={h.id}>
                <td className="p-3">{new Date(h.timestamp).toLocaleString()}</td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded text-xs ${h.success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    {h.success ? 'Success' : 'Failed'}
                  </span>
                </td>
                <td className="p-3 text-gray-400 text-xs">
                  {h.ip_address} <br/> {h.user_agent}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
