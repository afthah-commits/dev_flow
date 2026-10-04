import { api } from './axios';
import { Environment, EnvironmentVariable } from '../types/infrastructure';

export const environmentApi = {
  getEnvironments: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/environments`);
    return res.data as Environment[];
  },
  list: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/environments`);
    return res.data as Environment[];
  },
  getEnvironment: async (id: string) => {
    const res = await api.get(`/environments/${id}`);
    return res.data as Environment;
  },
  createEnvironment: async (projectId: string, data: Partial<Environment>) => {
    const res = await api.post(`/projects/${projectId}/environments`, data);
    return res.data as Environment;
  },
  create: async (projectId: string, data: Partial<Environment>) => {
    const res = await api.post(`/projects/${projectId}/environments`, data);
    return res.data as Environment;
  },
  updateEnvironment: async (id: string, data: Partial<Environment>) => {
    const res = await api.patch(`/environments/${id}`, data);
    return res.data as Environment;
  },
  update: async (projectId: string, envId: string, data: Partial<Environment>) => {
    const res = await api.patch(`/projects/${projectId}/environments/${envId}`, data);
    return res.data as Environment;
  },
  deleteEnvironment: async (id: string) => {
    await api.delete(`/environments/${id}`);
  },
  remove: async (projectId: string, envId: string) => {
    await api.delete(`/projects/${projectId}/environments/${envId}`);
  },
  getVariables: async (envId: string) => {
    const res = await api.get(`/environments/${envId}/variables`);
    return res.data as EnvironmentVariable[];
  }
};
