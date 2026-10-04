import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Uuid, Enum, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class DeploymentApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class DeploymentApproval(Base):
    __tablename__ = "deployment_approvals"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    deployment_id = Column(Uuid, ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(DeploymentApprovalStatus, native_enum=False), default=DeploymentApprovalStatus.PENDING, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    # Assuming deployment is accessible if needed, but not strictly required to define relationship back

class EnvironmentVariable(Base):
    __tablename__ = "environment_variables"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    environment_id = Column(Uuid, ForeignKey("environments.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String, nullable=False)
    encrypted_value = Column(String, nullable=False)
    is_secret = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ServiceHealthStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"

class ServiceHealth(Base):
    __tablename__ = "service_health"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    environment_id = Column(Uuid, ForeignKey("environments.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String, nullable=False)
    status = Column(Enum(ServiceHealthStatus, native_enum=False), default=ServiceHealthStatus.UNKNOWN, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    last_checked_at = Column(DateTime(timezone=True), server_default=func.now())
    error_message = Column(Text, nullable=True)

class DeploymentIncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"

class DeploymentIncident(Base):
    __tablename__ = "deployment_incidents"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    deployment_id = Column(Uuid, ForeignKey("deployments.id", ondelete="CASCADE"), nullable=True, index=True)
    environment_id = Column(Uuid, ForeignKey("environments.id", ondelete="CASCADE"), nullable=False, index=True)
    severity = Column(String, nullable=False) # e.g. HIGH, MEDIUM, LOW
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(DeploymentIncidentStatus, native_enum=False), default=DeploymentIncidentStatus.OPEN, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
