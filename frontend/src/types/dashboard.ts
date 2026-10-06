export interface DashboardWidgetPlacement {
  id: string;
  visible: boolean;
}

export interface DashboardLayoutResponse {
  widgets: DashboardWidgetPlacement[];
  defaults: string[];
  customized: boolean;
}
