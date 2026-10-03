import os

base_dir = "c:/personal_projects/devflow/frontend"
files = {}

files["src/types/task.ts"] = """export enum TaskStatus {
  TODO = "TODO",
  IN_PROGRESS = "IN_PROGRESS",
  IN_REVIEW = "IN_REVIEW",
  DONE = "DONE"
}

export enum TaskPriority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL"
}

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id?: string;
  creator_id: string;
  due_date?: string;
  labels: string[];
  created_at: string;
  updated_at: string;
}

export interface PaginatedTaskResponse {
  items: Task[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface TaskCreate {
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id?: string;
  due_date?: string;
  labels: string[];
}

export interface TaskUpdate extends Partial<TaskCreate> {}

export interface TaskStats {
  total: number;
  todo: number;
  in_progress: number;
  in_review: number;
  done: number;
  overdue: number;
}
"""

files["src/lib/taskApi.ts"] = """import { api } from "./axios";
import { Task, TaskCreate, TaskUpdate, PaginatedTaskResponse, TaskStatus, TaskPriority, TaskStats } from "../types/task";

export const taskApi = {
  list: async (projectId: string, params?: { 
    page?: number; 
    page_size?: number; 
    search?: string; 
    status?: TaskStatus; 
    priority?: TaskPriority; 
    assignee_id?: string;
    sort_by?: string; 
    sort_order?: string 
  }): Promise<PaginatedTaskResponse> => {
    const res = await api.get(`/projects/${projectId}/tasks`, { params });
    return res.data;
  },

  getStats: async (projectId: string): Promise<TaskStats> => {
    const res = await api.get(`/projects/${projectId}/tasks/stats`);
    return res.data;
  },

  get: async (projectId: string, id: string): Promise<Task> => {
    const res = await api.get(`/projects/${projectId}/tasks/${id}`);
    return res.data;
  },

  create: async (projectId: string, data: TaskCreate): Promise<Task> => {
    const res = await api.post(`/projects/${projectId}/tasks`, data);
    return res.data;
  },

  update: async (projectId: string, id: string, data: TaskUpdate): Promise<Task> => {
    const res = await api.patch(`/projects/${projectId}/tasks/${id}`, data);
    return res.data;
  },

  updateStatus: async (projectId: string, id: string, status: TaskStatus): Promise<Task> => {
    const res = await api.patch(`/projects/${projectId}/tasks/${id}/status`, { status });
    return res.data;
  },

  delete: async (projectId: string, id: string): Promise<void> => {
    await api.delete(`/projects/${projectId}/tasks/${id}`);
  }
};
"""

for path, content in files.items():
    with open(os.path.join(base_dir, path), "w", encoding="utf-8") as f:
        f.write(content)

print("Frontend Phase 3 part 1 generated.")
