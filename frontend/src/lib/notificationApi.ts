import { api } from './axios';
import { Notification, NotificationPreference } from '../types/notification';

export const notificationApi = {
  getNotifications: async (params?: { priority?: string, unread_only?: boolean, entity_type?: string }): Promise<Notification[]> => {
    const p = new URLSearchParams();
    if (params?.priority) p.append('priority', params.priority);
    if (params?.unread_only) p.append('unread_only', 'true');
    if (params?.entity_type) p.append('entity_type', params.entity_type);
    const res = await api.get(`/notifications?${p.toString()}`);
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
  markUnread: async (id: string): Promise<Notification> => {
    const res = await api.patch(`/notifications/${id}/unread`);
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
