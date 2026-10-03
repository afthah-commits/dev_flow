export interface Notification {
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
