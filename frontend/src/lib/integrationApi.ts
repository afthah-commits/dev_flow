import { api } from './axios';
import { Integration } from '../types/integration';

export const integrationApi = {
  list: async (orgId: string) => (await api.get('/integrations', { params: { organization_id: orgId } })).data as Integration[],
  create: async (orgId: string, data: any) => (await api.post('/integrations', data, { params: { organization_id: orgId } })).data as Integration,
  remove: async (id: string) => await api.delete(`/integrations/${id}`)
};
