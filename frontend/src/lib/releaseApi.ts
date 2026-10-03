import { api } from './axios';
import { Release, ReleaseReadiness, ReleaseTask, ReleasePR } from '../types/release';

export const releaseApi = {
  list: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/releases`);
    return res.data as Release[];
  },
  get: async (projectId: string, releaseId: string) => {
    const res = await api.get(`/projects/${projectId}/releases/${releaseId}`);
    return res.data as Release;
  },
  create: async (projectId: string, data: any) => {
    const res = await api.post(`/projects/${projectId}/releases`, data);
    return res.data as Release;
  },
  update: async (projectId: string, releaseId: string, data: any) => {
    const res = await api.patch(`/projects/${projectId}/releases/${releaseId}`, data);
    return res.data as Release;
  },
  remove: async (projectId: string, releaseId: string) => {
    await api.delete(`/projects/${projectId}/releases/${releaseId}`);
  },
  plan: async (releaseId: string) => {
    const res = await api.post(`/releases/${releaseId}/plan`);
    return res.data as Release;
  },
  ready: async (releaseId: string) => {
    const res = await api.post(`/releases/${releaseId}/ready`);
    return res.data as Release;
  },
  release: async (releaseId: string) => {
    const res = await api.post(`/releases/${releaseId}/release`);
    return res.data as Release;
  },
  cancel: async (releaseId: string) => {
    const res = await api.post(`/releases/${releaseId}/cancel`);
    return res.data as Release;
  },
  getTasks: async (releaseId: string) => {
    const res = await api.get(`/releases/${releaseId}/tasks`);
    return res.data as ReleaseTask[];
  },
  addTask: async (releaseId: string, taskId: string) => {
    const res = await api.post(`/releases/${releaseId}/tasks/${taskId}`);
    return res.data;
  },
  removeTask: async (releaseId: string, taskId: string) => {
    await api.delete(`/releases/${releaseId}/tasks/${taskId}`);
  },
  getPRs: async (releaseId: string) => {
    const res = await api.get(`/releases/${releaseId}/prs`);
    return res.data as ReleasePR[];
  },
  addPR: async (releaseId: string, data: { pr_number: number; pr_title?: string; pr_url?: string }) => {
    const res = await api.post(`/releases/${releaseId}/prs`, data);
    return res.data;
  },
  removePR: async (releaseId: string, prId: string) => {
    await api.delete(`/releases/${releaseId}/prs/${prId}`);
  },
  getNotes: async (releaseId: string) => {
    const res = await api.get(`/releases/${releaseId}/notes`);
    return res.data;
  },
  updateNotes: async (releaseId: string, notes: string) => {
    const res = await api.patch(`/releases/${releaseId}/notes`, { notes });
    return res.data;
  },
  getReadiness: async (releaseId: string) => {
    const res = await api.get(`/releases/${releaseId}/readiness`);
    return res.data as ReleaseReadiness;
  },
  generateAINotes: async (projectId: string, releaseId: string) => {
    const res = await api.post(`/ai/projects/${projectId}/releases/${releaseId}/generate-notes`);
    return res.data;
  },
  deploy: async (releaseId: string, data: { environment_id?: string; provider?: string }) => {
    const res = await api.post(`/releases/${releaseId}/deploy`, data);
    return res.data;
  }
};
