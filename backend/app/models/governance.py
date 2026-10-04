from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.db.base_class import Base

class OrganizationSecurityPolicy(Base):
    __tablename__ = "organization_security_policies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    require_mfa = Column(Boolean, default=False)
    allow_member_api_keys = Column(Boolean, default=True)
    allow_webhooks = Column(Boolean, default=True)
    allow_github_integration = Column(Boolean, default=True)
    allow_ai_features = Column(Boolean, default=True)
    allow_external_integrations = Column(Boolean, default=True)
    
    session_timeout_minutes = Column(Integer, default=1440)
    max_active_sessions = Column(Integer, default=5)
    password_expiry_days = Column(Integer, default=0)
    login_failure_threshold = Column(Integer, default=5)
    
    audit_retention_days = Column(Integer, default=90)
    data_retention_days = Column(Integer, default=365)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    organization = relationship("Organization")

class OrganizationDomain(Base):
    __tablename__ = "organization_domains"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    domain = Column(String, nullable=False)
    verification_token = Column(String, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization")

class OrganizationIdentityProvider(Base):
    __tablename__ = "organization_identity_providers"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_type = Column(String, nullable=False, default="OIDC")
    enabled = Column(Boolean, default=False)
    issuer_url = Column(String, nullable=True)
    client_id = Column(String, nullable=True)
    encrypted_client_secret = Column(String, nullable=True)
    configuration = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization")

class DataExportJob(Base):
    __tablename__ = "data_export_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="PENDING")
    export_type = Column(String, nullable=False)
    file_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    requested_by = relationship("User")

class SecurityApproval(Base):
    __tablename__ = "security_approvals"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    approved_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metadata_json = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

class OrganizationDeletionRequest(Base):
    __tablename__ = "organization_deletion_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="REQUESTED")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    requested_by = relationship("User")

class UserDeletionRequest(Base):
    __tablename__ = "user_deletion_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, default="REQUESTED")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")

