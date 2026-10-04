import { api } from './axios';
import { DeploymentIncident } from '../types/infrastructure';

export const incidentApi = {
  getIncidents: async (envId: string) => {
    const res = await api.get(`/environments/${envId}/incidents`);
    return res.data as DeploymentIncident[];
  },
  getAll: async () => {
    const res = await api.get(`/incidents`);
    return res.data as DeploymentIncident[];
  },
  createIncident: async (envId: string, data: Partial<DeploymentIncident>) => {
    const res = await api.post(`/environments/${envId}/incidents`, data);
    return res.data as DeploymentIncident;
  },
  updateIncident: async (id: string, data: Partial<DeploymentIncident>) => {
    const res = await api.patch(`/incidents/${id}`, data);
    return res.data as DeploymentIncident;
  }
};
