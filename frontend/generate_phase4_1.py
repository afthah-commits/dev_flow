import os

os.makedirs("c:/personal_projects/devflow/frontend/src/types", exist_ok=True)
with open("c:/personal_projects/devflow/frontend/src/types/github.ts", "w") as f:
    f.write("""export interface GitHubStatus {
  connected: boolean;
  github_username?: string;
  github_avatar_url?: string;
}

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  owner: string;
  html_url: string;
  description?: string;
  default_branch: string;
  private: boolean;
}

export interface GitHubRepositoryListResponse {
  items: GitHubRepository[];
  total: number;
  page: number;
}

export interface GitHubBranch {
  name: string;
  commit_sha: string;
  protected: boolean;
}

export interface GitHubCommit {
  sha: string;
  message: string;
  author_name: string;
  author_avatar?: string;
  date: string;
  html_url: string;
}

export interface GitHubPullRequest {
  number: number;
  title: string;
  state: string;
  author: string;
  created_at: string;
  updated_at: string;
  html_url: string;
}

export interface GitHubIssue {
  number: number;
  title: string;
  state: string;
  author: string;
  created_at: string;
  updated_at: string;
  html_url: string;
  labels: string[];
}

export interface GitHubConnectionResponse {
  project_id: string;
  github_repository_id: string;
  github_full_name: string;
  github_url: string;
  connected_at: string;
}
""")

with open("c:/personal_projects/devflow/frontend/src/lib/githubApi.ts", "w") as f:
    f.write("""import api from './axios';
import {
  GitHubStatus, GitHubRepositoryListResponse, GitHubConnectionResponse,
  GitHubBranch, GitHubCommit, GitHubPullRequest, GitHubIssue
} from '../types/github';

export const githubApi = {
  getStatus: async (): Promise<GitHubStatus> => {
    const res = await api.get('/github/status');
    return res.data;
  },
  connect: async (code: string, state: string): Promise<{message: string}> => {
    const res = await api.post('/github/connect', { code, state });
    return res.data;
  },
  disconnect: async (): Promise<{message: string}> => {
    const res = await api.delete('/github/disconnect');
    return res.data;
  },
  listRepositories: async (page: number = 1): Promise<GitHubRepositoryListResponse> => {
    const res = await api.get('/github/repositories', { params: { page } });
    return res.data;
  },
  
  // Project specific
  getProjectRepo: async (projectId: string): Promise<GitHubConnectionResponse> => {
    const res = await api.get(`/projects/${projectId}/github`);
    return res.data;
  },
  connectProjectRepo: async (projectId: string, repoFullName: string): Promise<GitHubConnectionResponse> => {
    const res = await api.post(`/projects/${projectId}/github`, { repo_full_name: repoFullName });
    return res.data;
  },
  disconnectProjectRepo: async (projectId: string): Promise<{message: string}> => {
    const res = await api.delete(`/projects/${projectId}/github`);
    return res.data;
  },
  listBranches: async (projectId: string): Promise<GitHubBranch[]> => {
    const res = await api.get(`/projects/${projectId}/github/branches`);
    return res.data;
  },
  listCommits: async (projectId: string): Promise<GitHubCommit[]> => {
    const res = await api.get(`/projects/${projectId}/github/commits`);
    return res.data;
  },
  listPullRequests: async (projectId: string, state: string = 'all'): Promise<GitHubPullRequest[]> => {
    const res = await api.get(`/projects/${projectId}/github/pulls`, { params: { state } });
    return res.data;
  },
  listIssues: async (projectId: string, state: string = 'all'): Promise<GitHubIssue[]> => {
    const res = await api.get(`/projects/${projectId}/github/issues`, { params: { state } });
    return res.data;
  }
};
""")

print("Phase 4 definitions created.")
