import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Uuid, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Automation(Base):
    __tablename__ = "automations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    enabled = Column(Boolean, default=True, index=True)
    trigger_type = Column(String, nullable=False, index=True)
    configuration = Column(JSON, nullable=True)
    conditions = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=False)
    execution_mode = Column(String, default="EVENT")  # IMMEDIATE, SCHEDULED, EVENT
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AutomationExecution(Base):
    __tablename__ = "automation_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    automation_id = Column(String, ForeignKey("automations.id"), nullable=False, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    trigger_event = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)  # QUEUED, RUNNING, SUCCESS, FAILED, PARTIAL, SKIPPED
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    execution_context = Column(JSON, nullable=True)
    idempotency_key = Column(String, nullable=True, index=True)

class AutomationActionExecution(Base):
    __tablename__ = "automation_action_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String, ForeignKey("automation_executions.id"), nullable=False, index=True)
    action_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

