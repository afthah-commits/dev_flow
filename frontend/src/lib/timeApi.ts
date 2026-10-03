import { api } from './axios';
import { ActiveTimer, TimeEntry, TimeSummary, ProjectTimeStats, ProductivityStats, TeamWorkload } from '../types/time';

export const timeApi = {
  getCurrentTimer: async () => {
    const response = await api.get('/time/timer/current');
    return response.data as ActiveTimer | null;
  },
  
  startTimer: async (data: { project_id: string; task_id?: string; description?: string }) => {
    const response = await api.post('/time/timer/start', data);
    return response.data as ActiveTimer;
  },
  
  stopTimer: async () => {
    const response = await api.post('/time/timer/stop');
    return response.data as TimeEntry;
  },
  
  discardTimer: async () => {
    const response = await api.post('/time/timer/discard');
    return response.data;
  },
  
  getEntries: async (params?: any) => {
    const response = await api.get('/time/entries', { params });
    return response.data as { items: TimeEntry[]; total: number };
  },
  
  createEntry: async (data: any) => {
    const response = await api.post('/time/entries', data);
    return response.data as TimeEntry;
  },
  
  updateEntry: async (id: string, data: any) => {
    const response = await api.patch(`/time/entries/${id}`, data);
    return response.data as TimeEntry;
  },
  
  deleteEntry: async (id: string) => {
    const response = await api.delete(`/time/entries/${id}`);
    return response.data;
  },
  
  getMySummary: async () => {
    const response = await api.get('/time/my-summary');
    return response.data as TimeSummary;
  },
  
  getProjectStats: async (projectId: string) => {
    const response = await api.get(`/projects/${projectId}/time/stats`);
    return response.data as ProjectTimeStats;
  },
  
  getProductivityStats: async (params?: any) => {
    const response = await api.get('/analytics/productivity', { params });
    return response.data as ProductivityStats;
  },
  
  getTeamWorkload: async (params?: any) => {
    const response = await api.get('/analytics/team-workload', { params });
    return response.data as TeamWorkload[];
  }
};
