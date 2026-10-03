import { api } from './axios';
import { Automation, AutomationExecution } from '../types/automation';

export const automationApi = {
  list: async (organizationId: string) => {
    const res = await api.get('/automations', { params: { organization_id: organizationId } });
    return res.data as Automation[];
  },
  get: async (id: string) => {
    const res = await api.get(/automations/\);
    return res.data as Automation;
  },
  create: async (organizationId: string, data: any) => {
    const res = await api.post('/automations', data, { params: { organization_id: organizationId } });
    return res.data as Automation;
  },
  update: async (id: string, data: any) => {
    const res = await api.patch(/automations/\, data);
    return res.data as Automation;
  },
  remove: async (id: string) => {
    await api.delete(/automations/\);
  },
  getExecutions: async (id: string) => {
    const res = await api.get(/automations/\/executions);
    return res.data as AutomationExecution[];
  },
  test: async (id: string, payload: any) => {
    const res = await api.post(/automations/\/test, payload);
    return res.data;
  },
  generateAI: async (prompt: string) => {
    const res = await api.post('/ai/automations/generate', { prompt });
    return res.data;
  }
};
