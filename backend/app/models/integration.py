import uuid
from sqlalchemy import Column, String, Uuid, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base

class Integration(Base):
    __tablename__ = "integrations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="ACTIVE")
    configuration = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_id = Column(String, ForeignKey("integrations.id"), nullable=False, index=True)
    encrypted_secret = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IntegrationLog(Base):
    __tablename__ = "integration_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_id = Column(String, ForeignKey("integrations.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
