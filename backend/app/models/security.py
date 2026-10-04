from sqlalchemy import Column, String, Boolean, DateTime, func, Uuid, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_system_role = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    organization = relationship("Organization")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    role_id = Column(Uuid, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission = Column(String, nullable=False, index=True)
    
    role = relationship("Role", back_populates="permissions")

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token_hash = Column(String, unique=True, nullable=False, index=True)
    device_name = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    operating_system = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User")

class LoginEvent(Base):
    __tablename__ = "login_events"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    email_attempted = Column(String, nullable=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    success = Column(Boolean, default=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    device_info = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
