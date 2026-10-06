import { api } from "./axios";
import {
  ProjectTemplate,
  ProjectTemplateCreate,
  ProjectTemplateUpdate,
  ProjectFromTemplateCreate,
  ProjectFromTemplateResponse,
} from "../types/template";

// Phase 44 — Project & Workspace Templates API.
// Backend routes live under /api/v1/templates/project/*; baseURL is already
// <host>/api/v1, so paths are base-relative.
export const projectTemplateApi = {
  list: async (includeArchived = false): Promise<ProjectTemplate[]> => {
    const res = await api.get<ProjectTemplate[]>("/templates/project", {
      params: includeArchived ? { include_archived: true } : undefined,
    });
    return res.data;
  },

  get: async (id: string): Promise<ProjectTemplate> => {
    const res = await api.get<ProjectTemplate>(`/templates/project/${id}`);
    return res.data;
  },

  create: async (data: ProjectTemplateCreate): Promise<ProjectTemplate> => {
    const res = await api.post<ProjectTemplate>("/templates/project", data);
    return res.data;
  },

  update: async (id: string, data: ProjectTemplateUpdate): Promise<ProjectTemplate> => {
    const res = await api.patch<ProjectTemplate>(`/templates/project/${id}`, data);
    return res.data;
  },

  archive: async (id: string): Promise<ProjectTemplate> => {
    const res = await api.post<ProjectTemplate>(`/templates/project/${id}/archive`);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/templates/project/${id}`);
  },

  createProject: async (
    id: string,
    data: ProjectFromTemplateCreate
  ): Promise<ProjectFromTemplateResponse> => {
    const res = await api.post<ProjectFromTemplateResponse>(
      `/templates/project/${id}/create-project`,
      data
    );
    return res.data;
  },
};
