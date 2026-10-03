import os

content = """import React, { useEffect, useState } from 'react';
import { githubApi } from '../lib/githubApi';
import { 
  GitHubConnectionResponse, GitHubBranch, GitHubCommit, 
  GitHubPullRequest, GitHubIssue, GitHubRepository 
} from '../types/github';
import { Project } from '../types/project';

interface Props {
  project: Project;
}

export function ProjectGitHub({ project }: Props) {
  const [repo, setRepo] = useState<GitHubConnectionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Connection UI states
  const [showSelector, setShowSelector] = useState(false);
  const [availableRepos, setAvailableRepos] = useState<GitHubRepository[]>([]);
  const [reposLoading, setReposLoading] = useState(false);
  const [connecting, setConnecting] = useState(false);

  // Tab states
  const [activeTab, setActiveTab] = useState<'overview' | 'branches' | 'commits' | 'pulls' | 'issues'>('overview');
  const [branches, setBranches] = useState<GitHubBranch[]>([]);
  const [commits, setCommits] = useState<GitHubCommit[]>([]);
  const [pulls, setPulls] = useState<GitHubPullRequest[]>([]);
  const [issues, setIssues] = useState<GitHubIssue[]>([]);
  const [dataLoading, setDataLoading] = useState(false);

  useEffect(() => {
    loadConnection();
  }, [project.id]);

  useEffect(() => {
    if (repo && !showSelector) {
      loadTabData(activeTab);
    }
  }, [repo, activeTab]);

  const loadConnection = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await githubApi.getProjectRepo(project.id);
      setRepo(res);
    } catch (e: any) {
      if (e.response?.status === 404) {
        setRepo(null); // Not connected
      } else {
        setError("Failed to load GitHub connection details.");
      }
    } finally {
      setLoading(false);
    }
  };

  const loadTabData = async (tab: string) => {
    try {
      setDataLoading(true);
      if (tab === 'branches' && branches.length === 0) {
        const res = await githubApi.listBranches(project.id);
        setBranches(res);
      } else if (tab === 'commits' && commits.length === 0) {
        const res = await githubApi.listCommits(project.id);
        setCommits(res);
      } else if (tab === 'pulls' && pulls.length === 0) {
        const res = await githubApi.listPullRequests(project.id);
        setPulls(res);
      } else if (tab === 'issues' && issues.length === 0) {
        const res = await githubApi.listIssues(project.id);
        setIssues(res);
      }
    } catch (e: any) {
      if (e.response?.status === 403) {
        setError("GitHub rate limit exceeded or access forbidden.");
      } else {
        setError(`Failed to load ${tab}.`);
      }
    } finally {
      setDataLoading(false);
    }
  };

  const handleOpenSelector = async () => {
    setShowSelector(true);
    setReposLoading(true);
    try {
      // Just load page 1 for simplicity in this phase
      const res = await githubApi.listRepositories(1);
      setAvailableRepos(res.items);
    } catch (e: any) {
      if (e.response?.status === 400) {
         setError("GitHub not connected globally. Go to Settings > Integrations.");
         setShowSelector(false);
      } else {
         setError("Failed to load repositories.");
      }
    } finally {
      setReposLoading(false);
    }
  };

  const handleConnect = async (full_name: string) => {
    try {
      setConnecting(true);
      await githubApi.connectProjectRepo(project.id, full_name);
      setShowSelector(false);
      await loadConnection();
    } catch (e) {
      setError("Failed to connect repository.");
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (window.confirm("Disconnect this repository?")) {
      try {
        await githubApi.disconnectProjectRepo(project.id);
        setRepo(null);
        setBranches([]);
        setCommits([]);
        setPulls([]);
        setIssues([]);
      } catch (e) {
        setError("Failed to disconnect repository.");
      }
    }
  };

  if (loading) return <div className="p-8 text-gray-400">Loading GitHub data...</div>;

  if (error) return <div className="p-4 bg-red-900/50 text-red-300 rounded">{error}</div>;

  if (!repo && !showSelector) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
        <h3 className="text-xl font-bold text-white mb-2">No GitHub Repository Connected</h3>
        <p className="text-gray-400 mb-6">Link a repository to view branches, commits, PRs, and issues directly in DevFlow.</p>
        <button onClick={handleOpenSelector} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium">
          Connect Repository
        </button>
      </div>
    );
  }

  if (showSelector) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-bold text-white">Select Repository</h3>
          <button onClick={() => setShowSelector(false)} className="text-gray-400 hover:text-white">Cancel</button>
        </div>
        {reposLoading ? (
          <div className="text-gray-400">Loading repositories...</div>
        ) : (
          <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
            {availableRepos.map(r => (
              <div key={r.id} className="flex justify-between items-center p-4 border border-gray-800 rounded-lg bg-gray-950/50 hover:border-gray-700">
                <div>
                  <h4 className="font-medium text-white">{r.full_name}</h4>
                  <p className="text-xs text-gray-500 mt-1">{r.private ? 'Private' : 'Public'} • {r.default_branch}</p>
                </div>
                <button 
                  onClick={() => handleConnect(r.full_name)}
                  disabled={connecting}
                  className="bg-gray-800 hover:bg-gray-700 text-white px-3 py-1 text-sm rounded border border-gray-700 disabled:opacity-50"
                >
                  Connect
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Repo Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 flex flex-col md:flex-row justify-between items-start md:items-center">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">{repo?.github_full_name}</h2>
          <p className="text-sm text-gray-400">Connected on {new Date(repo?.connected_at!).toLocaleDateString()}</p>
        </div>
        <div className="flex space-x-3 mt-4 md:mt-0">
          <a href={repo?.github_url} target="_blank" rel="noreferrer" className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white border border-gray-700 rounded transition-colors text-sm font-medium">
            Open in GitHub
          </a>
          <button onClick={handleDisconnect} className="px-4 py-2 bg-red-900/50 hover:bg-red-900/80 text-red-300 rounded transition-colors text-sm font-medium">
            Disconnect
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-gray-800 space-x-6">
        {['overview', 'branches', 'commits', 'pulls', 'issues'].map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={`pb-3 text-sm font-medium capitalize border-b-2 transition-colors ${
              activeTab === tab ? 'border-blue-500 text-white' : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 min-h-[400px]">
        {dataLoading ? (
          <div className="text-gray-400 animate-pulse">Fetching data from GitHub...</div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <div className="text-gray-300">
                <p>Repository is connected successfully. Select a tab above to view live data directly from GitHub.</p>
              </div>
            )}

            {activeTab === 'branches' && (
              <div className="space-y-2">
                {branches.length === 0 ? <p className="text-gray-400">No branches found.</p> : branches.map(b => (
                  <div key={b.name} className="flex justify-between items-center p-3 border border-gray-800 rounded bg-gray-950/50">
                    <span className="font-medium text-blue-400 font-mono">{b.name}</span>
                    <div className="flex space-x-4 text-xs text-gray-500">
                      {b.protected && <span className="text-amber-400 border border-amber-900/50 bg-amber-900/20 px-2 py-0.5 rounded">Protected</span>}
                      <span className="font-mono">{b.commit_sha.substring(0,7)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'commits' && (
              <div className="space-y-4">
                {commits.length === 0 ? <p className="text-gray-400">No commits found.</p> : commits.map(c => (
                  <div key={c.sha} className="flex space-x-4 border-b border-gray-800 pb-4 last:border-0">
                    {c.author_avatar ? (
                      <img src={c.author_avatar} alt="" className="w-10 h-10 rounded-full border border-gray-700" />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center font-bold text-gray-400">?</div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate"><a href={c.html_url} target="_blank" rel="noreferrer" className="hover:underline">{c.message}</a></p>
                      <p className="text-xs text-gray-500 mt-1">
                        <span className="font-medium text-gray-400">{c.author_name}</span> committed on {new Date(c.date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-xs font-mono text-gray-500"><a href={c.html_url} target="_blank" rel="noreferrer" className="hover:text-blue-400">{c.sha}</a></div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'pulls' && (
              <div className="space-y-3">
                {pulls.length === 0 ? <p className="text-gray-400">No pull requests found.</p> : pulls.map(p => (
                  <div key={p.number} className="p-4 border border-gray-800 rounded-lg bg-gray-950/50 flex justify-between">
                    <div>
                      <a href={p.html_url} target="_blank" rel="noreferrer" className="font-medium text-white hover:text-blue-400 block mb-1">
                        {p.title}
                      </a>
                      <p className="text-xs text-gray-500">#{p.number} opened by {p.author}</p>
                    </div>
                    <div>
                      <span className={`text-xs px-2 py-1 rounded-full border ${p.state === 'open' ? 'text-emerald-400 border-emerald-900 bg-emerald-900/30' : 'text-purple-400 border-purple-900 bg-purple-900/30'}`}>
                        {p.state}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'issues' && (
              <div className="space-y-3">
                {issues.length === 0 ? <p className="text-gray-400">No issues found.</p> : issues.map(i => (
                  <div key={i.number} className="p-4 border border-gray-800 rounded-lg bg-gray-950/50 flex flex-col">
                    <div className="flex justify-between mb-2">
                      <a href={i.html_url} target="_blank" rel="noreferrer" className="font-medium text-white hover:text-blue-400">
                        {i.title}
                      </a>
                      <span className={`text-xs px-2 py-1 rounded-full border ${i.state === 'open' ? 'text-emerald-400 border-emerald-900 bg-emerald-900/30' : 'text-gray-400 border-gray-700 bg-gray-800'}`}>
                        {i.state}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mb-2">#{i.number} opened by {i.author} on {new Date(i.created_at).toLocaleDateString()}</p>
                    {i.labels.length > 0 && (
                      <div className="flex gap-1 flex-wrap">
                        {i.labels.map(l => <span key={l} className="text-[10px] px-1.5 py-0.5 bg-gray-800 border border-gray-700 rounded text-gray-300">{l}</span>)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
"""

with open("c:/personal_projects/devflow/frontend/src/components/ProjectGitHub.tsx", "w") as f:
    f.write(content)
print("ProjectGitHub created")
