import { api } from './axios';
import { WebhookEndpoint } from '../types/webhook';

export const webhookApi = {
  list: async (orgId: string) => (await api.get('/webhooks', { params: { organization_id: orgId } })).data as WebhookEndpoint[],
  create: async (orgId: string, data: any) => (await api.post('/webhooks', data, { params: { organization_id: orgId } })).data as WebhookEndpoint,
  remove: async (id: string) => await api.delete(`/webhooks/${id}`)
};
