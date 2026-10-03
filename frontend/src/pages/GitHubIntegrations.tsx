import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { githubApi } from '../lib/githubApi';
import { GitHubStatus } from '../types/github';

export function GitHubSettings() {
  const [status, setStatus] = useState<GitHubStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const res = await githubApi.getStatus();
      setStatus(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = () => {
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID || 'dummy';
    const redirectUri = import.meta.env.VITE_GITHUB_REDIRECT_URI || 'http://localhost:5173/settings/integrations/github/callback';
    const state = Math.random().toString(36).substring(7);
    sessionStorage.setItem('github_oauth_state', state);
    const url = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=repo,read:user&state=${state}`;
    window.location.href = url;
  };

  const handleDisconnect = async () => {
    if (window.confirm("Are you sure you want to disconnect GitHub?")) {
      try {
        await githubApi.disconnect();
        loadStatus();
      } catch (e) {
        alert("Failed to disconnect");
      }
    }
  };

  if (loading) return <div className="text-gray-400 p-8">Loading GitHub status...</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-8 p-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Integrations</h1>
        <p className="text-gray-400">Connect DevFlow with your external tools.</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 flex flex-col md:flex-row items-center justify-between">
        <div className="flex items-center space-x-4 mb-4 md:mb-0">
          <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            GH
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">GitHub</h2>
            <p className="text-sm text-gray-400">Link repositories to projects.</p>
          </div>
        </div>
        
        {status?.connected ? (
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <img src={status.github_avatar_url} alt="Avatar" className="w-8 h-8 rounded-full border border-gray-700" />
              <span className="text-gray-300 font-medium">{status.github_username}</span>
            </div>
            <button onClick={handleDisconnect} className="px-4 py-2 bg-red-900/50 text-red-300 hover:bg-red-900/80 rounded transition-colors text-sm font-medium">
              Disconnect
            </button>
          </div>
        ) : (
          <button onClick={handleConnect} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors font-medium">
            Connect GitHub
          </button>
        )}
      </div>
    </div>
  );
}

export function GitHubCallback() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = params.get('code');
    const state = params.get('state');
    const savedState = sessionStorage.getItem('github_oauth_state');
    
    let mounted = true;

    if (!code || !state) {
      setTimeout(() => { if (mounted) setError("Invalid callback parameters."); }, 0);
      return;
    }
    if (state !== savedState) {
      setTimeout(() => { if (mounted) setError("Invalid state token. Possible CSRF attack."); }, 0);
      return;
    }

    githubApi.connect(code, state).then(() => {
      if (mounted) navigate('/settings/integrations');
    }).catch(e => {
      if (mounted) setError(e.response?.data?.detail || "Failed to connect");
    });
    
    return () => { mounted = false; };
  }, [params, navigate]);

  if (error) {
    return (
      <div className="p-8 text-center">
        <h2 className="text-red-400 text-xl font-bold mb-4">Authentication Failed</h2>
        <p className="text-gray-400 mb-4">{error}</p>
        <button onClick={() => navigate('/settings/integrations')} className="text-blue-400 hover:underline">Return to settings</button>
      </div>
    );
  }

  return <div className="p-8 text-gray-400 text-center text-lg font-medium">Completing GitHub connection...</div>;
}
