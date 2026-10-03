export type PipelineStatus = 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED';

export interface PipelineRun {
  id: string;
  organization_id: string;
  project_id: string;
  release_id?: string;
  deployment_id?: string;
  provider: string;
  branch?: string;
  commit_sha?: string;
  status: PipelineStatus;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  workflow_name?: string;
  workflow_url?: string;
  created_at: string;
}
