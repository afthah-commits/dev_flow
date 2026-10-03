import { api } from "./axios";

export const milestoneApi = {
  list: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/milestones`);
    return res.data;
  },
  get: async (projectId: string, milestoneId: string) => {
    const res = await api.get(`/projects/${projectId}/milestones/${milestoneId}`);
    return res.data;
  },
  create: async (projectId: string, data: any) => {
    const res = await api.post(`/projects/${projectId}/milestones`, data);
    return res.data;
  },
  update: async (projectId: string, milestoneId: string, data: any) => {
    const res = await api.patch(`/projects/${projectId}/milestones/${milestoneId}`, data);
    return res.data;
  },
  delete: async (projectId: string, milestoneId: string) => {
    const res = await api.delete(`/projects/${projectId}/milestones/${milestoneId}`);
    return res.data;
  },
  getStats: async (projectId: string, milestoneId: string) => {
    const res = await api.get(`/projects/${projectId}/milestones/${milestoneId}/stats`);
    return res.data;
  }
};
