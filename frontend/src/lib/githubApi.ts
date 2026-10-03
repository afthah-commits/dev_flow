import { api } from './axios';
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
