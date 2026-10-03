export enum ProjectStatus {
  PLANNING = "Planning",
  ACTIVE = "Active",
  ON_HOLD = "On Hold",
  COMPLETED = "Completed",
  ARCHIVED = "Archived"
}

export enum ProjectPriority {
  LOW = "Low",
  MEDIUM = "Medium",
  HIGH = "High",
  CRITICAL = "Critical"
}

export interface Project {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  description?: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  tech_stack: string[];
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
  task_stats?: {
    total: number;
    in_progress: number;
    done: number;
  };
}

export interface PaginatedProjectResponse {
  items: Project[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  tech_stack: string[];
  start_date?: string;
  end_date?: string;
}

export interface ProjectUpdate extends Partial<ProjectCreate> {}
