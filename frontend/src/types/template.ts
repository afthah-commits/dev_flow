import { TaskPriority } from "./task";

export interface ProjectTemplateTask {
  id: string;
  template_id: string;
  title: string;
  description?: string;
  priority: TaskPriority;
  position: number;
  label_names: string[];
  checklist_items: string[];
}

export interface ProjectTemplate {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  is_archived: boolean;
  created_by_id?: string;
  created_at?: string;
  updated_at?: string;
  tasks: ProjectTemplateTask[];
}

export interface ProjectTemplateTaskInput {
  title: string;
  description?: string;
  priority?: TaskPriority;
  position?: number;
  label_names?: string[];
  checklist_items?: string[];
}

export interface ProjectTemplateCreate {
  name: string;
  description?: string;
  tasks?: ProjectTemplateTaskInput[];
}

export interface ProjectTemplateUpdate extends Partial<ProjectTemplateCreate> {
  is_archived?: boolean;
}

export interface ProjectFromTemplateCreate {
  name: string;
  description?: string;
}

export interface ProjectFromTemplateResponse {
  project_id: string;
  name: string;
  slug: string;
  tasks_created: number;
}
