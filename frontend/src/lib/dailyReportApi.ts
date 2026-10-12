import { api } from './axios';
import { DailyReport, DailyReportCreate, DailyReportUpdate, DailyReportSummaryResponse, TeamDailyReportResponse, BlockerSummaryResponse, WeeklySummaryResponse } from '../types/dailyReport';

export const dailyReportApi = {
    getDailySummary: async (date: string, organizationId?: string): Promise<DailyReportSummaryResponse> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        const res = await api.get<DailyReportSummaryResponse>('/daily-reports/summary/daily', {
            params: { report_date: date },
            headers,
        });
        return res.data;
    },

    getWeeklySummary: async (startDate: string, organizationId?: string): Promise<WeeklySummaryResponse> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        const res = await api.get<WeeklySummaryResponse>('/daily-reports/summary/weekly', {
            params: { start_date: startDate },
            headers,
        });
        return res.data;
    },

    getTeamReports: async (date: string, organizationId?: string): Promise<TeamDailyReportResponse[]> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        const res = await api.get<TeamDailyReportResponse[]>('/daily-reports/team', {
            params: { report_date: date },
            headers,
        });
        return res.data;
    },

    getBlockers: async (days: number, organizationId?: string): Promise<BlockerSummaryResponse[]> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        const res = await api.get<BlockerSummaryResponse[]>('/daily-reports/blockers', {
            params: { days },
            headers,
        });
        return res.data;
    },

    list: async (organizationId?: string): Promise<DailyReport[]> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        const res = await api.get<DailyReport[]>('/daily-reports/', { headers });
        return res.data;
    },

    get: async (id: string, organizationId?: string): Promise<DailyReport> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        const res = await api.get<DailyReport>(`/daily-reports/${id}`, { headers });
        return res.data;
    },

    create: async (data: DailyReportCreate, organizationId?: string): Promise<DailyReport> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        const res = await api.post<DailyReport>('/daily-reports/', data, { headers });
        return res.data;
    },

    update: async (id: string, data: DailyReportUpdate, organizationId?: string): Promise<DailyReport> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        const res = await api.patch<DailyReport>(`/daily-reports/${id}`, data, { headers });
        return res.data;
    },

    delete: async (id: string, organizationId?: string): Promise<void> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        await api.delete(`/daily-reports/${id}`, { headers });
    },

    export: async (id: string, format: 'json' | 'csv', organizationId?: string): Promise<Blob | any> => {
        const headers: Record<string, string> = {};
        if (organizationId) headers['X-Organization-Id'] = organizationId;
        const res = await api.post(`/daily-reports/${id}/export`, null, {
            params: { format },
            headers,
            responseType: format === 'csv' ? 'blob' : 'json',
        });
        return res.data;
    }
};
