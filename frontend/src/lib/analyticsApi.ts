import { api } from './axios';
import { DashboardOverview, ProjectAnalyticsResponse, GitHubAnalyticsResponse } from '../types/analytics';

export const analyticsApi = {
  getDashboard: async (): Promise<DashboardOverview> => {
    const res = await api.get('/analytics/dashboard');
    return res.data;
  },
  getProjectAnalytics: async (projectId: string): Promise<ProjectAnalyticsResponse> => {
    const res = await api.get(`/analytics/projects/${projectId}`);
    return res.data;
  },
  getGitHubAnalytics: async (projectId: string): Promise<GitHubAnalyticsResponse> => {
    const res = await api.get(`/analytics/projects/${projectId}/github`);
    return res.data;
  }
};
