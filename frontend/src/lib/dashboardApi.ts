import { api } from "./axios";
import { DashboardLayoutResponse, DashboardWidgetPlacement } from "../types/dashboard";

// Phase 45 — personal dashboard layout preferences.
// baseURL is already <host>/api/v1, so paths are base-relative.
export const dashboardApi = {
  getLayout: async (): Promise<DashboardLayoutResponse> => {
    const res = await api.get<DashboardLayoutResponse>("/dashboard/layout");
    return res.data;
  },

  saveLayout: async (widgets: DashboardWidgetPlacement[]): Promise<DashboardLayoutResponse> => {
    const res = await api.put<DashboardLayoutResponse>("/dashboard/layout", { widgets });
    return res.data;
  },

  resetLayout: async (): Promise<DashboardLayoutResponse> => {
    const res = await api.delete<DashboardLayoutResponse>("/dashboard/layout");
    return res.data;
  },
};
