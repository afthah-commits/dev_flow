import { api } from "./axios";

export const sprintApi = {
  list: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/sprints`);
    return res.data;
  },
  get: async (projectId: string, sprintId: string) => {
    const res = await api.get(`/projects/${projectId}/sprints/${sprintId}`);
    return res.data;
  },
  create: async (projectId: string, data: any) => {
    const res = await api.post(`/projects/${projectId}/sprints`, data);
    return res.data;
  },
  update: async (projectId: string, sprintId: string, data: any) => {
    const res = await api.patch(`/projects/${projectId}/sprints/${sprintId}`, data);
    return res.data;
  },
  delete: async (projectId: string, sprintId: string) => {
    const res = await api.delete(`/projects/${projectId}/sprints/${sprintId}`);
    return res.data;
  },
  start: async (projectId: string, sprintId: string) => {
    const res = await api.post(`/projects/${projectId}/sprints/${sprintId}/start`);
    return res.data;
  },
  complete: async (projectId: string, sprintId: string, moveIncompleteTo?: string) => {
    const url = `/projects/${projectId}/sprints/${sprintId}/complete` + (moveIncompleteTo ? `?move_incomplete_to=${moveIncompleteTo}` : '');
    const res = await api.post(url);
    return res.data;
  },
  addTasks: async (projectId: string, sprintId: string, taskIds: string[]) => {
    const res = await api.post(`/projects/${projectId}/sprints/${sprintId}/tasks`, { task_ids: taskIds });
    return res.data;
  },
  removeTask: async (projectId: string, sprintId: string, taskId: string) => {
    const res = await api.delete(`/projects/${projectId}/sprints/${sprintId}/tasks/${taskId}`);
    return res.data;
  },
  getStats: async (projectId: string, sprintId: string) => {
    const res = await api.get(`/projects/${projectId}/sprints/${sprintId}/stats`);
    return res.data;
  },
  getBurndown: async (projectId: string, sprintId: string) => {
    const res = await api.get(`/projects/${projectId}/sprints/${sprintId}/burndown`);
    return res.data;
  }
};
