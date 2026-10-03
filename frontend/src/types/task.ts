export enum TaskStatus {
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
  position: number;
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

export interface TaskStats {
  total: number;
  todo: number;
  in_progress: number;
  in_review: number;
  done: number;
  overdue: number;
}
