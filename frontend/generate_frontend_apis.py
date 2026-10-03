import os

os.makedirs("c:/personal_projects/devflow/frontend/src/types", exist_ok=True)
os.makedirs("c:/personal_projects/devflow/frontend/src/lib", exist_ok=True)

types_analytics = """export interface DashboardOverview {
  total_projects: number;
  active_projects: number;
  completed_projects: number;
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  overdue_tasks: number;
  open_github_prs?: number;
  open_github_issues?: number;
}

export interface ProjectHealth {
  score: number;
  status: string;
}

export interface TaskTrendItem {
  date: string;
  created: number;
  completed: number;
  overdue: number;
}

export interface ProjectAnalyticsResponse {
  completion_rate: number;
  total_tasks: number;
  completed: number;
  in_progress: number;
  overdue: number;
  health: ProjectHealth;
  status_distribution: { status: string; count: number }[];
  priority_distribution: { priority: string; count: number }[];
  deadlines: {
    overdue: number;
    due_today: number;
    due_soon: number;
    future: number;
    no_deadline: number;
  };
  trends: TaskTrendItem[];
}

export interface GitHubAnalyticsResponse {
  recent_commits: number;
  open_prs: number;
  closed_prs: number;
  open_issues: number;
  closed_issues: number;
}
"""

types_notification = """export interface Notification {
  id: string;
  user_id: string;
  project_id?: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  read_at?: string;
}

export interface NotificationPreference {
  user_id: string;
  task_notifications: boolean;
  deadline_notifications: boolean;
  project_health_notifications: boolean;
  github_notifications: boolean;
  ai_notifications: boolean;
  updated_at?: string;
}
"""

lib_analytics = """import { api } from './axios';
import { DashboardOverview, ProjectAnalyticsResponse, GitHubAnalyticsResponse } from '../types/analytics';

export const analyticsApi = {
  getDashboard: async (): Promise<DashboardOverview> => {
    const res = await api.get('/analytics/dashboard');
    return res.data;
  },
  getProjectAnalytics: async (projectId: string): Promise<ProjectAnalyticsResponse> => {
    const res = await api.get(`/analytics/projects/${projectId}`);
    return res.data;
  },
  getGitHubAnalytics: async (projectId: string): Promise<GitHubAnalyticsResponse> => {
    const res = await api.get(`/analytics/projects/${projectId}/github`);
    return res.data;
  }
};
"""

lib_notification = """import { api } from './axios';
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
"""

with open("c:/personal_projects/devflow/frontend/src/types/analytics.ts", "w", encoding="utf-8") as f: f.write(types_analytics)
with open("c:/personal_projects/devflow/frontend/src/types/notification.ts", "w", encoding="utf-8") as f: f.write(types_notification)
with open("c:/personal_projects/devflow/frontend/src/lib/analyticsApi.ts", "w", encoding="utf-8") as f: f.write(lib_analytics)
with open("c:/personal_projects/devflow/frontend/src/lib/notificationApi.ts", "w", encoding="utf-8") as f: f.write(lib_notification)

print("Analytics and Notifications API/Types created")
