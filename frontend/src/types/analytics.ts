export interface DashboardOverview {
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
