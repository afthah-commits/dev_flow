import { api } from './axios';
import { Notification, NotificationPreference, NotificationSummary, ActionItem } from '../types/notification';

export const notificationApi = {
  getNotifications: async (params?: {
    priority?: string;
    unread_only?: boolean;
    entity_type?: string;
    notification_type?: string;
    important?: boolean;
    action_required?: boolean;
    date_from?: string;
    date_to?: string;
    skip?: number;
    limit?: number;
  }): Promise<Notification[]> => {
    const p = new URLSearchParams();
    if (params?.priority) p.append('priority', params.priority);
    if (params?.unread_only) p.append('unread_only', 'true');
    if (params?.entity_type) p.append('entity_type', params.entity_type);
    if (params?.notification_type) p.append('notification_type', params.notification_type);
    if (params?.important !== undefined) p.append('important', String(params.important));
    if (params?.action_required !== undefined) p.append('action_required', String(params.action_required));
    if (params?.date_from) p.append('date_from', params.date_from);
    if (params?.date_to) p.append('date_to', params.date_to);
    if (params?.skip !== undefined) p.append('skip', String(params.skip));
    if (params?.limit !== undefined) p.append('limit', String(params.limit));
    const res = await api.get(`/notifications?${p.toString()}`);
    return res.data;
  },

  getUnreadCount: async (): Promise<{ count: number }> => {
    const res = await api.get('/notifications/unread-count');
    return res.data;
  },

  getSummary: async (): Promise<NotificationSummary> => {
    const res = await api.get('/notifications/summary');
    return res.data;
  },

  getActionCenter: async (): Promise<ActionItem[]> => {
    const res = await api.get('/notifications/action-center');
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

  markImportant: async (id: string): Promise<Notification> => {
    const res = await api.patch(`/notifications/${id}/important`);
    return res.data;
  },

  markUnimportant: async (id: string): Promise<Notification> => {
    const res = await api.patch(`/notifications/${id}/unimportant`);
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
  },
};
