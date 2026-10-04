import { api } from './axios';
import { ServiceHealth } from '../types/infrastructure';

export const infrastructureApi = {
  getServiceHealth: async (envId: string) => {
    const res = await api.get(`/environments/${envId}/services/health`);
    return res.data as ServiceHealth[];
  },
  getAnalytics: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/infrastructure/analytics`);
    return res.data;
  }
};
