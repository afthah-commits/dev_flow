from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class OrganizationSecurityPolicyBase(BaseModel):
    require_mfa: bool = False
    allow_member_api_keys: bool = True
    allow_webhooks: bool = True
    allow_github_integration: bool = True
    allow_ai_features: bool = True
    allow_external_integrations: bool = True
    session_timeout_minutes: int = 1440
    max_active_sessions: int = 5
    password_expiry_days: int = 0
    login_failure_threshold: int = 5
    audit_retention_days: int = 90
    data_retention_days: int = 365

class OrganizationSecurityPolicyUpdate(BaseModel):
    require_mfa: Optional[bool] = None
    allow_member_api_keys: Optional[bool] = None
    allow_webhooks: Optional[bool] = None
    allow_github_integration: Optional[bool] = None
    allow_ai_features: Optional[bool] = None
    allow_external_integrations: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    max_active_sessions: Optional[int] = None
    password_expiry_days: Optional[int] = None
    login_failure_threshold: Optional[int] = None
    audit_retention_days: Optional[int] = None
    data_retention_days: Optional[int] = None

class OrganizationSecurityPolicyResponse(OrganizationSecurityPolicyBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class OrganizationDomainBase(BaseModel):
    domain: str

class OrganizationDomainCreate(OrganizationDomainBase):
    pass

class OrganizationDomainResponse(OrganizationDomainBase):
    id: str
    organization_id: str
    verification_token: str
    verified_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DataExportJobBase(BaseModel):
    export_type: str

class DataExportJobCreate(DataExportJobBase):
    pass

class DataExportJobResponse(DataExportJobBase):
    id: str
    organization_id: str
    requested_by_id: Optional[str] = None
    status: str
    file_metadata: Dict[str, Any] = {}
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class SecurityApprovalBase(BaseModel):
    action_type: str
    metadata_json: Dict[str, Any] = {}

class SecurityApprovalCreate(SecurityApprovalBase):
    pass

class SecurityApprovalResponse(SecurityApprovalBase):
    id: str
    organization_id: str
    requested_by_id: Optional[str] = None
    status: str
    approved_by_id: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
