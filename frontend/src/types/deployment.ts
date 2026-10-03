export type DeploymentStatus = 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED' | 'ROLLED_BACK';
export type DeploymentProvider = 'MOCK' | 'GITHUB_ACTIONS' | 'MANUAL';

export interface Deployment {
  id: string;
  organization_id: string;
  project_id: string;
  release_id?: string;
  environment_id?: string;
  status: DeploymentStatus;
  deployment_url?: string;
  commit_sha?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  triggered_by_id?: string;
  provider: DeploymentProvider;
  error_message?: string;
  previous_deployment_id?: string;
  created_at: string;
}
