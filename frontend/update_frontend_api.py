import os

types_task = """export enum TaskStatus {
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

export enum TaskDependencyType {
  BLOCKS = "BLOCKS",
  RELATES_TO = "RELATES_TO"
}

export interface UserAvatarInfo {
  id: string;
  full_name: string;
  email: string;
}

export interface Label {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  color: string;
  created_at?: string;
  updated_at?: string;
}

export interface ChecklistItem {
  id: string;
  task_id: string;
  text: string;
  completed: boolean;
  position: float;
  created_at?: string;
  updated_at?: string;
}

export interface TaskDependency {
  id: string;
  source_id: string;
  target_id: string;
  dependency_type: TaskDependencyType;
  created_at?: string;
}

export interface Task {
  id: string;
  task_key?: string;
  project_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id?: string;
  creator_id: string;
  updated_by_id?: string;
  due_date?: string;
  
  parent_id?: string;
  estimate_points?: number;
  estimate_hours?: number;
  actual_hours?: number;
  position: number;
  is_blocked: boolean;
  recurring_config?: any;
  
  labels?: string[]; // Legacy
  labels_rel?: Label[];
  watchers?: UserAvatarInfo[];
  checklists?: ChecklistItem[];
  blocks?: TaskDependency[];
  blocked_by?: TaskDependency[];
  subtasks?: Task[];
  
  created_at: string;
  updated_at?: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  assignee_id?: string;
  due_date?: string;
  labels?: string[];
  
  parent_id?: string;
  estimate_points?: number;
  estimate_hours?: number;
  actual_hours?: number;
  position?: number;
  recurring_config?: any;
  label_ids?: string[];
}

export interface PaginatedTaskResponse {
  items: Task[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}
"""

lib_task_api = """import { api } from './axios';
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
"""

with open("c:/personal_projects/devflow/frontend/src/types/task.ts", "w", encoding="utf-8") as f:
    f.write(types_task)
    
with open("c:/personal_projects/devflow/frontend/src/lib/taskApi.ts", "w", encoding="utf-8") as f:
    f.write(lib_task_api)

print("Frontend task types and APIs updated.")
