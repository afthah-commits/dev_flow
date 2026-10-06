export interface Notification {
  id: string;
  user_id: string;
  organization_id?: string;
  project_id?: string;
  type: string;
  priority: string;
  entity_type?: string;
  entity_id?: string;
  title: string;
  message: string;
  read: boolean;
  action_required: boolean;
  important: boolean;
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
  daily_report_notifications: boolean;
  deployment_notifications: boolean;
  release_notifications: boolean;
  job_notifications: boolean;
  automation_notifications: boolean;
  workflow_approval_notifications: boolean;
  client_request_notifications: boolean;
  team_activity_notifications: boolean;
  updated_at?: string;
}

export interface NotificationSummary {
  unread: number;
  important: number;
  action_required: number;
  pending_approvals: number;
  failed_jobs: number;
}

export interface ActionItem {
  id: string;
  type: string;
  title: string;
  description: string;
  entity_type: string;
  entity_id?: string;
  priority: string;
  created_at: string;
  action_url?: string;
}
