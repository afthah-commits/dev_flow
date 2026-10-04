import { api } from './axios';
import { Deployment, DeploymentApproval } from '../types/infrastructure';

export const deploymentApi = {
  list: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/deployments`);
    return res.data as Deployment[];
  },
  getDeployments: async (envId: string) => {
    const res = await api.get(`/environments/${envId}/deployments`);
    return res.data as Deployment[];
  },
  getDeployment: async (id: string) => {
    const res = await api.get(`/deployments/${id}`);
    return res.data as Deployment;
  },
  get: async (id: string) => {
    const res = await api.get(`/deployments/${id}`);
    return res.data as Deployment;
  },
  triggerDeployment: async (envId: string, data: Partial<Deployment>) => {
    const res = await api.post(`/environments/${envId}/deployments`, data);
    return res.data as Deployment;
  },
  rollbackDeployment: async (id: string) => {
    const res = await api.post(`/deployments/${id}/rollback`);
    return res.data as Deployment;
  },
  rollback: async (id: string) => {
    const res = await api.post(`/deployments/${id}/rollback`);
    return res.data as Deployment;
  },
  getApprovals: async (deploymentId: string) => {
    const res = await api.get(`/deployments/${deploymentId}/approvals`);
    return res.data as DeploymentApproval[];
  },
  approve: async (deploymentId: string) => {
    const res = await api.post(`/deployments/${deploymentId}/approve`);
    return res.data as DeploymentApproval;
  },
  reject: async (deploymentId: string) => {
    const res = await api.post(`/deployments/${deploymentId}/reject`);
    return res.data as DeploymentApproval;
  }
};
