import { api } from './axios';
import { Report, Dashboard, DashboardWidget } from '../types/report';

export const reportApi = {
  getReports: async (orgId: string) => {
    const res = await api.get<Report[]>(`/reports/`, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  createReport: async (orgId: string, data: Partial<Report>) => {
    const res = await api.post<Report>(`/reports/`, data, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  getReportData: async (orgId: string, reportId: string, filters: any = {}) => {
    const res = await api.post(`/reports/${reportId}/data`, filters, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },

  getDashboards: async (orgId: string) => {
    const res = await api.get<Dashboard[]>(`/dashboards/`, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },

  createDashboard: async (orgId: string, data: Partial<Dashboard>) => {
    const res = await api.post<Dashboard>(`/dashboards/`, data, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },

  addWidget: async (orgId: string, dashboardId: string, data: Partial<DashboardWidget>) => {
    const res = await api.post<DashboardWidget>(`/dashboards/${dashboardId}/widgets`, data, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  }
};

