import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum, JSON, Text, Integer, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class WorkflowEntityType(str, enum.Enum):
    TASK = "TASK"
    CLIENT_REQUEST = "CLIENT_REQUEST"
    RELEASE = "RELEASE"
    DEPLOYMENT = "DEPLOYMENT"
    CUSTOM = "CUSTOM"

class WorkflowConditionType(str, enum.Enum):
    ALL = "ALL"
    ANY = "ANY"
    NOT = "NOT"
    FIELD_EQUALS = "FIELD_EQUALS"
    FIELD_GREATER = "FIELD_GREATER"

class WorkflowActionType(str, enum.Enum):
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    SEND_NOTIFICATION = "SEND_NOTIFICATION"
    CREATE_AUDIT_EVENT = "CREATE_AUDIT_EVENT"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    TRIGGER_AUTOMATION = "TRIGGER_AUTOMATION"

class WorkflowApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    CANCELLED = "CANCELLED"

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    entity_type = Column(Enum(WorkflowEntityType, native_enum=False), default=WorkflowEntityType.TASK, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    states = relationship("WorkflowState", back_populates="workflow", cascade="all, delete-orphan")
    transitions = relationship("WorkflowTransition", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowState(Base):
    __tablename__ = "workflow_states"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    key = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, default=0, nullable=False)
    color = Column(String, nullable=True)
    is_initial = Column(Boolean, default=False, nullable=False)
    is_terminal = Column(Boolean, default=False, nullable=False)

    workflow = relationship("Workflow", back_populates="states")
    
    __table_args__ = (UniqueConstraint('workflow_id', 'key', name='uq_workflow_state_key'),)

class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    from_state_id = Column(UUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False)
    to_state_id = Column(UUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, default=0, nullable=False)
    requires_approval = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    workflow = relationship("Workflow", back_populates="transitions")
    conditions = relationship("WorkflowCondition", back_populates="transition", cascade="all, delete-orphan")
    actions = relationship("WorkflowAction", back_populates="transition", cascade="all, delete-orphan")

class WorkflowCondition(Base):
    __tablename__ = "workflow_conditions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    transition_id = Column(UUID(as_uuid=True), ForeignKey("workflow_transitions.id", ondelete="CASCADE"), nullable=False, index=True)
    condition_type = Column(Enum(WorkflowConditionType, native_enum=False), nullable=False)
    field = Column(String, nullable=True)
    operator = Column(String, nullable=True)
    value = Column(String, nullable=True)
    configuration = Column(JSON, nullable=True)

    transition = relationship("WorkflowTransition", back_populates="conditions")

class WorkflowAction(Base):
    __tablename__ = "workflow_actions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    transition_id = Column(UUID(as_uuid=True), ForeignKey("workflow_transitions.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(Enum(WorkflowActionType, native_enum=False), nullable=False)
    configuration = Column(JSON, nullable=True)
    position = Column(Integer, default=0, nullable=False)

    transition = relationship("WorkflowTransition", back_populates="actions")

class WorkflowApproval(Base):
    __tablename__ = "workflow_approvals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_transition_id = Column(UUID(as_uuid=True), ForeignKey("workflow_transitions.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approver_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    status = Column(Enum(WorkflowApprovalStatus, native_enum=False), default=WorkflowApprovalStatus.PENDING, nullable=False)
    comment = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime, nullable=True)

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    current_state_id = Column(UUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="ACTIVE", nullable=False) # ACTIVE, COMPLETED, FAILED
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

class WorkflowExecutionEvent(Base):
    __tablename__ = "workflow_execution_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False) # TRANSITION, APPROVAL_REQUESTED, etc.
    from_state_id = Column(UUID(as_uuid=True), nullable=True)
    to_state_id = Column(UUID(as_uuid=True), nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

# Custom Fields Models
class CustomFieldType(str, enum.Enum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"
    SELECT = "SELECT"
    MULTI_SELECT = "MULTI_SELECT"
    USER = "USER"
    PROJECT = "PROJECT"
    CLIENT = "CLIENT"

class CustomField(Base):
    __tablename__ = "custom_fields"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    key = Column(String, nullable=False)
    field_type = Column(Enum(CustomFieldType, native_enum=False), nullable=False)
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    configuration = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (UniqueConstraint('organization_id', 'key', name='uq_org_custom_field_key'),)

class CustomFieldValue(Base):
    __tablename__ = "custom_field_values"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    custom_field_id = Column(UUID(as_uuid=True), ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    value = Column(JSON, nullable=True) # Stored as JSON to handle all types (string, array, number, bool)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class WorkflowForm(Base):
    __tablename__ = "workflow_forms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    configuration = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class WorkflowFormField(Base):
    __tablename__ = "workflow_form_fields"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    form_id = Column(UUID(as_uuid=True), ForeignKey("workflow_forms.id", ondelete="CASCADE"), nullable=False, index=True)
    custom_field_id = Column(UUID(as_uuid=True), ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, default=0, nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)
