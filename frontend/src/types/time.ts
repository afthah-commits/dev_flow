export interface ActiveTimer {
  id: string;
  organization_id: string;
  user_id: string;
  project_id: string;
  task_id?: string;
  description?: string;
  started_at: string;
  elapsed_seconds: number;
}

export interface TimeEntry {
  id: string;
  organization_id: string;
  user_id: string;
  project_id: string;
  task_id?: string;
  sprint_id?: string;
  description?: string;
  started_at: string;
  ended_at: string;
  duration_seconds: number;
  billable: boolean;
  source: 'TIMER' | 'MANUAL';
  created_at: string;
}

export interface TimeSummary {
  today_hours: number;
  week_hours: number;
  month_hours: number;
  tracked_hours: number;
  billable_hours: number;
  completed_tasks: number;
  active_timer?: ActiveTimer;
}

export interface ProjectTimeStats {
  total_tracked_hours: number;
  billable_hours: number;
  non_billable_hours: number;
  active_users: number;
  tasks_tracked: number;
  avg_time_per_task: number;
  estimated_hours: number;
  estimate_variance: number;
}

export interface ProductivityStats {
  total_hours: number;
  active_days: number;
  tasks_completed: number;
  tasks_worked_on: number;
  avg_hours_per_day: number;
  avg_hours_per_task: number;
  estimated_hours: number;
  completion_rate: number;
}

export interface TeamWorkload {
  user_id: string;
  user_name: string;
  tracked_hours: number;
  assigned_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  estimated_hours: number;
  workload_percentage: number;
}
