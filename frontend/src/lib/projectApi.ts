import { api } from "./axios";
import { Project, ProjectCreate, ProjectUpdate, PaginatedProjectResponse, ProjectStatus, ProjectPriority } from "../types/project";

export const projectApi = {
  list: async (params?: { 
    page?: number; 
    page_size?: number; 
    search?: string; 
    status?: ProjectStatus; 
    priority?: ProjectPriority; 
    sort_by?: string; 
    sort_order?: string 
  }): Promise<PaginatedProjectResponse> => {
    const res = await api.get("/projects", { params });
    return res.data;
  },

  get: async (id: string): Promise<Project> => {
    const res = await api.get(`/projects/${id}`);
    return res.data;
  },

  create: async (data: ProjectCreate): Promise<Project> => {
    const res = await api.post("/projects", data);
    return res.data;
  },

  update: async (id: string, data: ProjectUpdate): Promise<Project> => {
    const res = await api.patch(`/projects/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`);
  }
};
