import React, { useEffect, useState, useCallback } from "react";
import { githubApi } from "../lib/githubApi";

interface ProjectGitHubProps {
  project: { id: string; name?: string };
}

type Tab = "branches" | "commits";

export function ProjectGitHub({ project }: ProjectGitHubProps) {
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const [repo, setRepo] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [selecting, setSelecting] = useState(false);
  const [repositories, setRepositories] = useState<any[]>([]);
  const [repositoriesLoading, setRepositoriesLoading] = useState(false);

  const [tab, setTab] = useState<Tab>("branches");
  const [branches, setBranches] = useState<any[]>([]);
  const [commits, setCommits] = useState<any[]>([]);
  const [tabLoading, setTabLoading] = useState(false);

  const loadConnection = useCallback(async () => {
    if (!project?.id) return;
    setLoading(true);
    setError(null);
    try {
      const conn = await githubApi.getProjectRepo(project.id);
      setRepo(conn);
      setConnected(true);
    } catch (e: any) {
      if (e?.response?.status === 404) {
        setConnected(false);
        setRepo(null);
      } else {
        setError("Failed to load the GitHub connection.");
        setConnected(false);
        setRepo(null);
      }
    } finally {
      setLoading(false);
    }
  }, [project?.id]);

  useEffect(() => {
    loadConnection();
  }, [loadConnection]);

  const openSelector = async () => {
    setSelecting(true);
    setRepositoriesLoading(true);
    try {
      const res = await githubApi.listRepositories(1);
      setRepositories(res?.items ?? []);
    } catch {
      setRepositories([]);
      setError("Failed to load your GitHub repositories.");
    } finally {
      setRepositoriesLoading(false);
    }
  };

  const connect = async (fullName: string) => {
    try {
      await githubApi.connectProjectRepo(project.id, fullName);
      setSelecting(false);
      await loadConnection();
    } catch {
      setError("Failed to connect the repository.");
    }
  };

  const disconnect = async () => {
    try {
      await githubApi.disconnectProjectRepo(project.id);
      await loadConnection();
    } catch {
      setError("Failed to disconnect the repository.");
    }
  };

  const switchTab = (next: Tab) => {
    setTab(next);
    setTabLoading(true);
    const request =
      next === "branches"
        ? githubApi.listBranches(project.id).then(setBranches)
        : githubApi.listCommits(project.id).then(setCommits);
    request
      .catch(() => setError(`Failed to load ${next}.`))
      .finally(() => setTabLoading(false));
  };

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-sm text-gray-400">
        Loading GitHub integration…
      </div>
    );
  }

  if (!connected) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6" data-testid="github-not-connected">
        {error && <p className="mb-3 text-sm text-red-400">{error}</p>}
        <h3 className="text-lg font-semibold text-white mb-1">No GitHub Repository Connected</h3>
        <p className="text-sm text-gray-400 mb-4">
          Connect a repository to view branches, commits, pull requests, and issues for this project.
        </p>
        <button
          onClick={openSelector}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
        >
          Connect Repository
        </button>

        {selecting && (
          <div className="mt-5 border-t border-gray-800 pt-4" data-testid="repo-selector">
            <h4 className="text-sm font-semibold text-gray-200 mb-2">Select Repository</h4>
            {repositoriesLoading ? (
              <p className="text-sm text-gray-500">Loading repositories…</p>
            ) : repositories.length === 0 ? (
              <p className="text-sm text-gray-500">No repositories available.</p>
            ) : (
              <ul className="space-y-1 max-h-64 overflow-y-auto">
                {repositories.map((r) => (
                  <li key={r.id}>
                    <button
                      onClick={() => connect(r.full_name)}
                      className="w-full text-left rounded px-3 py-2 text-sm text-gray-200 hover:bg-gray-800"
                    >
                      {r.full_name}
                      {r.private && <span className="ml-2 text-xs text-amber-400">private</span>}
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <button
              onClick={() => setSelecting(false)}
              className="mt-3 rounded border border-gray-700 px-3 py-1.5 text-sm text-gray-300 hover:bg-gray-800"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg" data-testid="github-connected">
      {error && <p className="px-6 pt-4 text-sm text-red-400">{error}</p>}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div>
          <h3 className="text-lg font-semibold text-white">{repo?.github_full_name}</h3>
          {repo?.connected_at && (
            <p className="text-xs text-gray-500">
              Connected {new Date(repo.connected_at).toLocaleString()}
            </p>
          )}
        </div>
        <button
          onClick={disconnect}
          className="rounded border border-red-800 px-3 py-1.5 text-sm text-red-300 hover:bg-red-900/30"
        >
          Disconnect
        </button>
      </div>

      <div className="flex gap-4 px-6 pt-3">
        {(["branches", "commits"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => switchTab(t)}
            className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? "border-blue-500 text-blue-400" : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="p-6">
        {tabLoading && <p className="text-sm text-gray-500">Loading {tab}…</p>}

        {!tabLoading && tab === "branches" && (
          branches.length === 0 ? (
            <p className="text-sm text-gray-500">No branches found.</p>
          ) : (
            <ul className="space-y-2">
              {branches.map((b: any) => (
                <li key={b.name} className="flex items-center justify-between rounded border border-gray-800 px-3 py-2">
                  <span className="font-mono text-sm text-gray-200">{b.name}</span>
                  {b.protected && (
                    <span className="rounded bg-purple-900/50 px-2 py-0.5 text-xs text-purple-300">Protected</span>
                  )}
                </li>
              ))}
            </ul>
          )
        )}

        {!tabLoading && tab === "commits" && (
          commits.length === 0 ? (
            <p className="text-sm text-gray-500">No commits found.</p>
          ) : (
            <ul className="space-y-2">
              {commits.map((c: any) => (
                <li key={c.sha ?? c.commit_sha} className="rounded border border-gray-800 px-3 py-2">
                  <p className="text-sm text-gray-200">{c.message ?? c.commit?.message}</p>
                  <p className="text-xs text-gray-500 font-mono">{(c.sha ?? c.commit_sha ?? "").slice(0, 7)}</p>
                </li>
              ))}
            </ul>
          )
        )}
      </div>
    </div>
  );
}

export default ProjectGitHub;
