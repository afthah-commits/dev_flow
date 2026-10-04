import { api } from './axios';
import { APIKey } from '../types/api_key';

export const apiKeyApi = {
  list: async (orgId: string) => (await api.get('/api_keys', { params: { organization_id: orgId } })).data as APIKey[],
  create: async (orgId: string, data: any) => (await api.post('/api_keys', data, { params: { organization_id: orgId } })).data as APIKey,
  revoke: async (id: string) => await api.post('/api_keys/' + id + '/revoke')
};
