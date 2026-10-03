import { api } from "./axios";

export const backlogApi = {
  get: async (projectId: string, params?: any) => {
    const res = await api.get(`/projects/${projectId}/backlog`, { params });
    return res.data;
  }
};

export const roadmapApi = {
  get: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/roadmap`);
    return res.data;
  }
};
