import { api } from './axios';
import { Notification, NotificationPreference } from '../types/notification';

export const notificationApi = {
  getNotifications: async (): Promise<Notification[]> => {
    const res = await api.get('/notifications');
    return res.data;
  },
  getUnreadCount: async (): Promise<{ count: number }> => {
    const res = await api.get('/notifications/unread-count');
    return res.data;
  },
  markRead: async (id: string): Promise<Notification> => {
    const res = await api.patch(`/notifications/${id}/read`);
    return res.data;
  },
  markAllRead: async (): Promise<void> => {
    await api.patch('/notifications/read-all');
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/notifications/${id}`);
  },
  getPreferences: async (): Promise<NotificationPreference> => {
    const res = await api.get('/notifications/preferences');
    return res.data;
  },
  updatePreferences: async (data: Partial<NotificationPreference>): Promise<NotificationPreference> => {
    const res = await api.patch('/notifications/preferences', data);
    return res.data;
  }
};
