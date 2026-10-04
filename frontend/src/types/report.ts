export enum ReportType {
  PROJECT_OVERVIEW = "PROJECT_OVERVIEW",
  TASK_ANALYTICS = "TASK_ANALYTICS",
  SPRINT_REPORT = "SPRINT_REPORT",
  TEAM_WORKLOAD = "TEAM_WORKLOAD",
  TIME_TRACKING = "TIME_TRACKING",
  PRODUCTIVITY = "PRODUCTIVITY",
  GITHUB_DELIVERY = "GITHUB_DELIVERY",
  RELEASE_DELIVERY = "RELEASE_DELIVERY",
  AUDIT_ACTIVITY = "AUDIT_ACTIVITY",
  EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
}

export interface Report {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  report_type: ReportType;
  configuration: Record<string, any>;
  created_by_id?: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardWidget {
  id: string;
  dashboard_id: string;
  widget_type: string;
  title: string;
  configuration: Record<string, any>;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  created_at: string;
  updated_at: string;
}

export interface Dashboard {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  is_default: boolean;
  created_by_id?: string;
  created_at: string;
  updated_at: string;
  widgets: DashboardWidget[];
}
