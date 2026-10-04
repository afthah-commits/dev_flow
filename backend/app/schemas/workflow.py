from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.workflow import (
    WorkflowEntityType,
    WorkflowConditionType,
    WorkflowActionType,
    WorkflowApprovalStatus,
    WorkflowStateType,
    WorkflowVersionStatus,
)

# ---------------------------------------------------------------------------
# Phase 29 (existing) schemas — unchanged, kept for backward compatibility
# ---------------------------------------------------------------------------

class WorkflowStateBase(BaseModel):
    name: str
    key: str
    description: Optional[str] = None
    position: int = 0
    color: Optional[str] = None
    is_initial: bool = False
    is_terminal: bool = False

class WorkflowStateCreate(WorkflowStateBase):
    pass

class WorkflowStateResponse(WorkflowStateBase):
    id: UUID
    workflow_id: UUID

    class Config:
        from_attributes = True

class WorkflowTransitionBase(BaseModel):
    name: str
    from_state_id: UUID
    to_state_id: UUID
    position: int = 0
    requires_approval: bool = False

class WorkflowTransitionCreate(WorkflowTransitionBase):
    pass

class WorkflowTransitionResponse(WorkflowTransitionBase):
    id: UUID
    workflow_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    entity_type: WorkflowEntityType
    is_active: bool = True

class WorkflowCreate(WorkflowBase):
    states: Optional[List[WorkflowStateCreate]] = []
    transitions: Optional[List[WorkflowTransitionCreate]] = []

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class WorkflowResponse(WorkflowBase):
    id: UUID
    organization_id: UUID
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    states: List[WorkflowStateResponse] = []
    transitions: List[WorkflowTransitionResponse] = []

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Phase 30 — Visual Workflow Studio schemas
# ---------------------------------------------------------------------------

SAFE_OPERATORS = [
    "EQUALS",
    "NOT_EQUALS",
    "CONTAINS",
    "NOT_CONTAINS",
    "GREATER_THAN",
    "LESS_THAN",
    "GREATER_THAN_OR_EQUAL",
    "LESS_THAN_OR_EQUAL",
    "IS_EMPTY",
    "IS_NOT_EMPTY",
]

FORM_FIELD_TYPES = [
    "TEXT", "TEXTAREA", "NUMBER", "DATE", "DATETIME", "SELECT",
    "MULTI_SELECT", "CHECKBOX", "RADIO", "USER", "TEAM", "PROJECT",
    "TASK", "CLIENT", "FILE", "CUSTOM_FIELD",
]


class ApprovalConfigSchema(BaseModel):
    """Approval requirements for states/transitions (Phase 30 approval builder)."""
    required: bool = False
    approver_type: Optional[str] = None  # ROLE | TEAM | USER
    organization_role: Optional[str] = None
    team_id: Optional[UUID] = None
    approver_user_id: Optional[UUID] = None
    minimum_approvals: int = 1
    timeout_hours: Optional[int] = None
    on_reject: str = "BLOCK"  # BLOCK | CANCEL | RETURN_TO_PREVIOUS


class ConditionSchema(BaseModel):
    """Safe condition. Operators are restricted to SAFE_OPERATORS (no eval)."""
    field: str
    operator: str
    value: Optional[str] = None
    condition_type: WorkflowConditionType = WorkflowConditionType.FIELD_EQUALS


class ActionSchema(BaseModel):
    action_type: WorkflowActionType
    configuration: Optional[Dict[str, Any]] = None
    position: int = 0
    enabled: bool = True


class StateStudioCreate(BaseModel):
    name: str
    key: Optional[str] = None  # generated from name when omitted
    description: Optional[str] = None
    position: int = 0
    color: Optional[str] = None
    state_type: WorkflowStateType = WorkflowStateType.NORMAL
    is_initial: bool = False
    is_terminal: bool = False
    approval_config: Optional[ApprovalConfigSchema] = None
    available_actions: Optional[List[str]] = None


class StateStudioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None
    color: Optional[str] = None
    state_type: Optional[WorkflowStateType] = None
    is_initial: Optional[bool] = None
    is_terminal: Optional[bool] = None
    approval_config: Optional[ApprovalConfigSchema] = None
    available_actions: Optional[List[str]] = None


class StateStudioResponse(StateStudioCreate):
    id: UUID
    workflow_id: UUID
    key: str
    incoming_count: int = 0
    outgoing_count: int = 0

    class Config:
        from_attributes = True


class TransitionStudioCreate(BaseModel):
    name: str
    from_state_id: UUID
    to_state_id: UUID
    description: Optional[str] = None
    requires_approval: bool = False
    approval_config: Optional[ApprovalConfigSchema] = None
    conditions: Optional[List[ConditionSchema]] = []
    actions: Optional[List[ActionSchema]] = []


class TransitionStudioUpdate(BaseModel):
    name: Optional[str] = None
    from_state_id: Optional[UUID] = None
    to_state_id: Optional[UUID] = None
    description: Optional[str] = None
    requires_approval: Optional[bool] = None
    approval_config: Optional[ApprovalConfigSchema] = None
    conditions: Optional[List[ConditionSchema]] = None
    actions: Optional[List[ActionSchema]] = None


class ConditionResponse(ConditionSchema):
    id: UUID

    class Config:
        from_attributes = True


class ActionResponse(ActionSchema):
    id: UUID
    configuration: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TransitionStudioResponse(TransitionStudioCreate):
    id: UUID
    workflow_id: UUID
    from_state_id: UUID
    to_state_id: UUID
    conditions: List[ConditionResponse] = []
    actions: List[ActionResponse] = []
    approval_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class StateLayoutItem(BaseModel):
    state_id: UUID
    x: float = 0
    y: float = 0


class LayoutSaveRequest(BaseModel):
    positions: List[StateLayoutItem]


class StateLayoutResponse(BaseModel):
    state_id: UUID
    x: float
    y: float

    class Config:
        from_attributes = True


class ValidationIssue(BaseModel):
    severity: str  # PASS | WARNING | ERROR
    code: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    entity_name: Optional[str] = None


class ValidationResult(BaseModel):
    status: str  # PASS | WARNING | ERROR
    can_publish: bool
    issues: List[ValidationIssue]
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudioGraph(BaseModel):
    """Full studio payload: graph + layout + metadata."""
    workflow: WorkflowResponse
    states: List[StateStudioResponse] = []
    transitions: List[TransitionStudioResponse] = []
    layouts: List[StateLayoutResponse] = []
    forms: List["FormSummary"] = []
    versions: List["WorkflowVersionResponse"] = []
    published_version_number: Optional[int] = None
    validation: Optional[ValidationResult] = None


class WorkflowVersionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    version_number: int
    status: WorkflowVersionStatus
    change_note: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowVersionDetail(WorkflowVersionResponse):
    snapshot: Optional[Dict[str, Any]] = None


class VersionCreateRequest(BaseModel):
    change_note: Optional[str] = None


class SimulationStep(BaseModel):
    step_number: int
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    transition_name: Optional[str] = None
    condition_evaluations: List[Dict[str, Any]] = []
    conditions_result: Optional[bool] = None
    actions: List[Dict[str, Any]] = []
    result: str = "PASS"  # PASS | FAIL | BLOCKED
    detail: Optional[str] = None


class SimulationRequest(BaseModel):
    entity_type: str = "TASK"
    entity_id: Optional[UUID] = None
    sample_data: Optional[Dict[str, Any]] = {}
    start_state_id: Optional[UUID] = None
    target_state_id: Optional[UUID] = None


class SimulationResponse(BaseModel):
    dry_run: bool = True
    entity_type: str
    workflow_version_id: Optional[UUID] = None
    start_state: Optional[str] = None
    end_state: Optional[str] = None
    steps: List[SimulationStep] = []
    status: str = "PASS"  # PASS | FAIL | BLOCKED
    summary: Optional[str] = None


class FormFieldDefinition(BaseModel):
    """One field inside a workflow form (Phase 30 advanced form builder)."""
    id: str
    type: str  # one of FORM_FIELD_TYPES
    label: str
    description: Optional[str] = None
    required: bool = False
    default_value: Optional[Any] = None
    placeholder: Optional[str] = None
    position: int = 0
    width: str = "FULL"  # FULL | HALF | THIRD
    # Conditional visibility: field appears only when the rule passes.
    visibility: Optional[Dict[str, Any]] = None  # {field, operator, value, action: SHOW|HIDE}
    validation: Optional[Dict[str, Any]] = None  # {min, max, minLength, maxLength, pattern, message}
    options: Optional[List[str]] = None  # SELECT / RADIO choices
    custom_field_id: Optional[UUID] = None  # link to existing CustomField


class FormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    fields: List[FormFieldDefinition] = []


class FormUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    fields: Optional[List[FormFieldDefinition]] = None


class FormResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workflow_id: Optional[UUID]
    name: str
    description: Optional[str] = None
    is_active: bool
    configuration: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FormSummary(BaseModel):
    id: UUID
    name: str
    is_active: bool
    field_count: int = 0


class FormValidationResult(BaseModel):
    valid: bool
    issues: List[ValidationIssue] = []


class ExecutionEventResponse(BaseModel):
    id: UUID
    event_type: str
    from_state_id: Optional[UUID] = None
    to_state_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    workflow_version_id: Optional[UUID] = None
    entity_type: str
    entity_id: UUID
    current_state_id: Optional[UUID] = None
    status: str
    trigger_source: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True


class ExecutionDetail(ExecutionResponse):
    events: List[ExecutionEventResponse] = []


class ExecutionStartRequest(BaseModel):
    entity_type: str = "TASK"
    entity_id: UUID
    trigger_source: Optional[str] = "MANUAL"


class TransitionExecuteRequest(BaseModel):
    entity_id: UUID
    context: Optional[Dict[str, Any]] = {}


class WorkflowAnalyticsResponse(BaseModel):
    total_workflows: int = 0
    published_workflows: int = 0
    draft_workflows: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    active_executions: int = 0
    avg_execution_seconds: Optional[float] = None
    failure_rate: Optional[float] = None
    approval_rejection_rate: Optional[float] = None
    most_used_workflow: Optional[Dict[str, Any]] = None
    most_used_transition: Optional[Dict[str, Any]] = None
    state_durations: List[Dict[str, Any]] = []
    executions_by_day: List[Dict[str, Any]] = []


class AIWorkflowSuggestion(BaseModel):
    """Advisory-only AI output. Never auto-saved, auto-published or executed."""
    name: str
    entity_type: str = "TASK"
    description: Optional[str] = None
    states: List[Dict[str, Any]] = []
    transitions: List[Dict[str, Any]] = []
    form_fields: List[Dict[str, Any]] = []
    notes: List[str] = []
    preview_only: bool = True


class AIApplyRequest(BaseModel):
    """Explicit user action to apply a reviewed AI suggestion as a DRAFT."""
    suggestion: AIWorkflowSuggestion


StudioGraph.model_rebuild()
