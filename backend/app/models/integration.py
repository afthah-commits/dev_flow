import uuid
from sqlalchemy import Column, String, Uuid, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.sql import func
from app.db.base_class import Base

class Integration(Base):
    __tablename__ = "integrations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="ACTIVE")
    enabled = Column(Boolean, default=True)
    configuration = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(String, nullable=True)

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

class IntegrationEvent(Base):
    __tablename__ = "integration_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IntegrationDelivery(Base):
    __tablename__ = "integration_deliveries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, ForeignKey("integration_events.id"), nullable=False, index=True)
    integration_id = Column(String, ForeignKey("integrations.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="PENDING", index=True)
    attempts = Column(Integer, default=0)
    response_status = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    idempotency_key = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)

class EmailDelivery(Base):
    __tablename__ = "email_deliveries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    to_address = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(String, nullable=False)
    status = Column(String, nullable=False, default="DELIVERED")
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
