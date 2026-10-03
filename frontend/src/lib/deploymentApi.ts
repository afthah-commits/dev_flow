import { api } from './axios';
import { Deployment } from '../types/deployment';

export const deploymentApi = {
  list: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/deployments`);
    return res.data as Deployment[];
  },
  get: async (deploymentId: string) => {
    const res = await api.get(`/deployments/${deploymentId}`);
    return res.data as Deployment;
  },
  rollback: async (deploymentId: string) => {
    const res = await api.post(`/deployments/${deploymentId}/rollback`);
    return res.data as Deployment;
  }
};
