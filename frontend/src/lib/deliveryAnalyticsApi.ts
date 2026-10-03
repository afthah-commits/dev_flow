import { api } from './axios';
import { DeliveryMetrics, DoraMetrics } from '../types/deliveryAnalytics';

export const deliveryAnalyticsApi = {
  getDeliveryMetrics: async (projectId?: string) => {
    const res = await api.get('/analytics/delivery', { params: projectId ? { project_id: projectId } : {} });
    return res.data as DeliveryMetrics;
  },
  getDoraMetrics: async (projectId?: string) => {
    const res = await api.get('/analytics/dora', { params: projectId ? { project_id: projectId } : {} });
    return res.data as DoraMetrics;
  }
};
