import { DailyReport, DailyReportCreate, DailyReportUpdate } from '../types/dailyReport';

const API_BASE_URL = '/api/v1/daily-reports';

export const dailyReportApi = {
    list: async (organizationId: string): Promise<DailyReport[]> => {
        const response = await fetch(`${API_BASE_URL}/`, {
            headers: {
                'X-Organization-Id': organizationId,
            },
        });
        if (!response.ok) throw new Error('Failed to fetch daily reports');
        return response.json();
    },

    get: async (id: string, organizationId: string): Promise<DailyReport> => {
        const response = await fetch(`${API_BASE_URL}/${id}`, {
            headers: {
                'X-Organization-Id': organizationId,
            },
        });
        if (!response.ok) throw new Error('Failed to fetch daily report');
        return response.json();
    },

    create: async (data: DailyReportCreate, organizationId: string): Promise<DailyReport> => {
        const response = await fetch(`${API_BASE_URL}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Organization-Id': organizationId,
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create daily report');
        }
        return response.json();
    },

    update: async (id: string, data: DailyReportUpdate, organizationId: string): Promise<DailyReport> => {
        const response = await fetch(`${API_BASE_URL}/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-Organization-Id': organizationId,
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update daily report');
        }
        return response.json();
    },

    delete: async (id: string, organizationId: string): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/${id}`, {
            method: 'DELETE',
            headers: {
                'X-Organization-Id': organizationId,
            },
        });
        if (!response.ok) throw new Error('Failed to delete daily report');
    },

    export: async (id: string, format: 'json' | 'csv', organizationId: string): Promise<Blob | any> => {
        const response = await fetch(`${API_BASE_URL}/${id}/export?format=${format}`, {
            method: 'POST',
            headers: {
                'X-Organization-Id': organizationId,
            },
        });
        if (!response.ok) throw new Error('Failed to export daily report');
        
        if (format === 'csv') {
            return response.blob();
        }
        return response.json();
    }
};
