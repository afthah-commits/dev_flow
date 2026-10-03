export interface Notification {
  id: string;
  user_id: string;
  project_id?: string;
  type: string;
  priority: string;
  entity_type?: string;
  entity_id?: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  read_at?: string;
}

export interface NotificationPreference {
  user_id: string;
  task_notifications: boolean;
  task_assignments: boolean;
  deadline_notifications: boolean;
  project_health_notifications: boolean;
  github_notifications: boolean;
  ai_notifications: boolean;
  sprint_events: boolean;
  milestone_events: boolean;
  security_events: boolean;
  digest_notifications: boolean;
  updated_at?: string;
}
