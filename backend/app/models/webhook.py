import uuid
from sqlalchemy import Column, String, Uuid, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.sql import func
from app.db.base_class import Base

class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    encrypted_secret = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    subscribed_events = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = Column(String, ForeignKey("webhook_endpoints.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    http_status = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    attempt_count = Column(Integer, default=1)
    error_message = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    response_body = Column(String, nullable=True)
    idempotency_key = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
