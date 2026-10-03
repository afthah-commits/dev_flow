import { api } from './axios';
import { Environment } from '../types/environment';

export const environmentApi = {
  list: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/environments`);
    return res.data as Environment[];
  },
  create: async (projectId: string, data: any) => {
    const res = await api.post(`/projects/${projectId}/environments`, data);
    return res.data as Environment;
  },
  update: async (projectId: string, envId: string, data: any) => {
    const res = await api.patch(`/projects/${projectId}/environments/${envId}`, data);
    return res.data as Environment;
  },
  remove: async (projectId: string, envId: string) => {
    await api.delete(`/projects/${projectId}/environments/${envId}`);
  }
};
