export type ReleaseStatus = 'DRAFT' | 'READY' | 'APPROVED' | 'DEPLOYING' | 'DEPLOYED' | 'FAILED' | 'ROLLED_BACK' | 'CANCELLED';
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
  deployment_timestamp?: string;
  rollback_timestamp?: string;
  approved_by_id?: string;
  created_by_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface ReadinessCheck {
  name: string;
  status: 'PASS' | 'WARNING' | 'FAIL';
  message: string;
}

export interface ReleaseReadiness {
  ready: boolean;
  score: number;
  checks: ReadinessCheck[];
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

export interface ReleaseApproval {
  id: string;
  release_id: string;
  requested_by_id: string;
  reviewer_id: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'REVOKED';
  comment?: string;
  created_at: string;
  updated_at?: string;
}
