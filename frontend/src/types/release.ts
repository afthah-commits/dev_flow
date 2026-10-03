export type ReleaseStatus = 'DRAFT' | 'PLANNED' | 'READY' | 'RELEASED' | 'CANCELLED';
export type ReleaseType = 'MAJOR' | 'MINOR' | 'PATCH' | 'HOTFIX';

export interface Release {
  id: string;
  organization_id: string;
  project_id: string;
  name: string;
  version: string;
  description?: string;
  status: ReleaseStatus;
  release_type: ReleaseType;
  target_environment?: string;
  git_tag?: string;
  target_commit_sha?: string;
  planned_at?: string;
  released_at?: string;
  created_by_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface ReleaseReadiness {
  score: number;
  task_completion_pct: number;
  pipeline_health_pct: number;
  blocked_tasks_penalty: number;
  deployment_health_pct: number;
  sprint_completion_pct: number;
  explanations: string[];
}

export interface ReleaseTask {
  id: string;
  title: string;
  status?: string;
  priority?: string;
}

export interface ReleasePR {
  id: string;
  pr_number: number;
  pr_title?: string;
  pr_url?: string;
}
