import { api } from './axios';
import { Integration, WebhookEndpoint, ApiUsage } from '../types/integrationHub';

export const integrationHubApi = {
  getIntegrations: async (orgId: string) => {
    const res = await api.get<Integration[]>('/integrations', {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  createIntegration: async (orgId: string, data: Partial<Integration>) => {
    const res = await api.post<Integration>('/integrations', data, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  deleteIntegration: async (orgId: string, id: string) => {
    await api.delete(`/integrations/${id}`, {
      headers: { 'X-Organization-Id': orgId }
    });
  },

  enableIntegration: async (orgId: string, id: string) => {
    const res = await api.post<Integration>(`/integrations/${id}/enable`, {}, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  disableIntegration: async (orgId: string, id: string) => {
    const res = await api.post<Integration>(`/integrations/${id}/disable`, {}, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },

  testIntegration: async (orgId: string, id: string) => {
    const res = await api.post(`/integrations/${id}/test`, {}, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },

  getApiUsage: async (orgId: string) => {
    const res = await api.get<ApiUsage>('/integrations/usage/analytics', {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  }
};
