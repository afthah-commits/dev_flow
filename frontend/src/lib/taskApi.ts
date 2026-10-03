import { api } from './axios';
import { Task, TaskCreate, PaginatedTaskResponse, TaskStatus } from '../types/task';

export const taskApi = {
  list: async (projectId: string, params?: any) => {
    const res = await api.get<PaginatedTaskResponse>(`/projects/${projectId}/tasks`, { params });
    return res.data;
  },
  
  get: async (projectId: string, taskId: string) => {
    const res = await api.get<Task>(`/projects/${projectId}/tasks/${taskId}`);
    return res.data;
  },
  
  create: async (projectId: string, data: TaskCreate) => {
    const res = await api.post<Task>(`/projects/${projectId}/tasks`, data);
    return res.data;
  },
  
  update: async (projectId: string, taskId: string, data: Partial<TaskCreate>) => {
    const res = await api.patch<Task>(`/projects/${projectId}/tasks/${taskId}`, data);
    return res.data;
  },
  
  updateStatus: async (projectId: string, taskId: string, status: TaskStatus, position?: number) => {
    const res = await api.patch<Task>(`/projects/${projectId}/tasks/${taskId}/status`, { status, position });
    return res.data;
  },
  
  delete: async (projectId: string, taskId: string) => {
    const res = await api.delete(`/projects/${projectId}/tasks/${taskId}`);
    return res.data;
  },
  
  getStats: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/tasks/stats`);
    return res.data;
  },
  
  addChecklist: async (projectId: string, taskId: string, text: string) => {
    const res = await api.post(`/projects/${projectId}/tasks/${taskId}/checklists`, { text });
    return res.data;
  },
  
  updateChecklist: async (projectId: string, taskId: string, itemId: string, completed: boolean) => {
    const res = await api.patch(`/projects/${projectId}/tasks/${taskId}/checklists/${itemId}`, { completed });
    return res.data;
  },
  
  deleteChecklist: async (projectId: string, taskId: string, itemId: string) => {
    const res = await api.delete(`/projects/${projectId}/tasks/${taskId}/checklists/${itemId}`);
    return res.data;
  },
  
  addDependency: async (projectId: string, taskId: string, targetId: string, type = "BLOCKS") => {
    const res = await api.post(`/projects/${projectId}/tasks/${taskId}/dependencies`, { target_id: targetId, dependency_type: type });
    return res.data;
  },
  
  deleteDependency: async (projectId: string, taskId: string, depId: string) => {
    const res = await api.delete(`/projects/${projectId}/tasks/${taskId}/dependencies/${depId}`);
    return res.data;
  },
  
  watch: async (projectId: string, taskId: string) => {
    const res = await api.post(`/projects/${projectId}/tasks/${taskId}/watchers`);
    return res.data;
  },
  
  unwatch: async (projectId: string, taskId: string) => {
    const res = await api.delete(`/projects/${projectId}/tasks/${taskId}/watchers`);
    return res.data;
  },
  
  bulkUpdate: async (projectId: string, taskIds: string[], data: any) => {
    const res = await api.post(`/projects/${projectId}/tasks/bulk/update`, { task_ids: taskIds, ...data });
    return res.data;
  },
  
  bulkDelete: async (projectId: string, taskIds: string[]) => {
    const res = await api.post(`/projects/${projectId}/tasks/bulk/delete`, { task_ids: taskIds });
    return res.data;
  }
};
