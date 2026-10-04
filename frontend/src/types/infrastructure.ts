export type EnvironmentType = 'production' | 'staging' | 'qa' | 'development' | 'sandbox' | 'custom';
export type DeploymentStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'rolled_back' | 'canceled';
export type ApprovalStatus = 'pending' | 'approved' | 'rejected';
export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low';
export type IncidentStatus = 'open' | 'investigating' | 'resolved' | 'closed';

export interface Environment {
  id: string;
  projectId: string;
  name: string;
  type: EnvironmentType;
  description?: string;
  createdAt: string;
  created_at: string;
  organization_id: string;
  project_id: string;
  provider: string;
  is_default: boolean;
  is_active: boolean;
  updatedAt: string;
}

export interface Deployment {
  id: string;
  environmentId: string;
  releaseId?: string;
  version: string;
  status: DeploymentStatus;
  trigger: 'manual' | 'automatic' | 'webhook';
  triggeredBy?: string;
  startedAt?: string;
  completedAt?: string;
  logsUrl?: string;
  rollbackOf?: string;
  createdAt: string;
  created_at: string;
  organization_id: string;
  project_id: string;
  provider: string;
  is_default: boolean;
  is_active: boolean;
  updatedAt: string;
  commitHash?: string;
}

export interface DeploymentApproval {
  id: string;
  deploymentId: string;
  approverId: string;
  status: ApprovalStatus;
  comments?: string;
  createdAt: string;
  created_at: string;
  organization_id: string;
  project_id: string;
  provider: string;
  is_default: boolean;
  is_active: boolean;
  updatedAt: string;
}

export interface EnvironmentVariable {
  id: string;
  environmentId: string;
  key: string;
  value: string;
  isSecret: boolean;
  createdAt: string;
  created_at: string;
  organization_id: string;
  project_id: string;
  provider: string;
  is_default: boolean;
  is_active: boolean;
  updatedAt: string;
}

export interface ServiceHealth {
  id: string;
  environmentId: string;
  serviceName: string;
  status: 'healthy' | 'degraded' | 'down';
  lastCheckedAt: string;
  details?: string;
}

export interface DeploymentIncident {
  id: string;
  deploymentId?: string;
  environmentId: string;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  reportedBy: string;
  createdAt: string;
  created_at: string;
  organization_id: string;
  project_id: string;
  provider: string;
  is_default: boolean;
  is_active: boolean;
  updatedAt: string;
}
