export interface OrganizationSecurityPolicy {
  id: string;
  organization_id: string;
  require_mfa: boolean;
  allow_member_api_keys: boolean;
  allow_webhooks: boolean;
  allow_github_integration: boolean;
  allow_ai_features: boolean;
  allow_external_integrations: boolean;
  session_timeout_minutes: number;
  max_active_sessions: number;
  password_expiry_days: number;
  login_failure_threshold: number;
  audit_retention_days: number;
  data_retention_days: number;
  created_at: string;
  updated_at: string;
}

export interface OrganizationDomain {
  id: string;
  organization_id: string;
  domain: string;
  verification_token: string;
  verified_at: string | null;
  created_at: string;
}

export interface DataExportJob {
  id: string;
  organization_id: string;
  requested_by_id: string | null;
  status: string;
  export_type: string;
  file_metadata: any;
  created_at: string;
  completed_at: string | null;
  expires_at: string | null;
}
