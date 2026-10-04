from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.api.deps import get_db, get_current_user, get_current_organization_id, require_organization_member
from app.models.user import User
from app.models.organization import OrganizationRole
from app.models.workflow import (
    Workflow, WorkflowState, WorkflowStateType, WorkflowTransition, WorkflowCondition,
    WorkflowConditionType, WorkflowAction, WorkflowActionType, WorkflowApproval,
    WorkflowExecution, WorkflowExecutionEvent, WorkflowVersion, WorkflowVersionStatus,
    WorkflowStateLayout, WorkflowForm, WorkflowFormField,
)
from app.models.task import Task
from app.models.audit import AuditEvent
from app.schemas.workflow import (
    WorkflowResponse, WorkflowCreate, WorkflowUpdate,
    StateStudioCreate, StateStudioUpdate, StateStudioResponse,
    TransitionStudioCreate, TransitionStudioUpdate, TransitionStudioResponse,
    ConditionSchema, ActionSchema,
    LayoutSaveRequest, StateLayoutResponse,
    StudioGraph, ValidationResult, ValidationIssue,
    WorkflowVersionResponse, WorkflowVersionDetail, VersionCreateRequest,
    SimulationRequest, SimulationResponse,
    FormCreate, FormUpdate, FormResponse,
    ExecutionStartRequest, ExecutionDetail, ExecutionResponse, ExecutionEventResponse,
    TransitionExecuteRequest,
    WorkflowAnalyticsResponse,
    AIWorkflowSuggestion, AIApplyRequest,
)
from app.services import workflow_studio as studio
from app.services.workflow_permissions import get_workflow_permission
from app.services.audit_service import record_event
from app.models.workflow import WorkflowEntityType
from app.schemas.workflow import SAFE_OPERATORS

router = APIRouter()

WORKFLOW_ROLES = [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER]


def _get_workflow_or_404(db: Session, workflow_id: UUID, org_id: Optional[UUID]) -> Workflow:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.organization_id == org_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


def _state_out(s: WorkflowState) -> Dict[str, Any]:
    transitions = s.workflow.transitions if s.workflow else []
    return {
        "id": s.id,
        "workflow_id": s.workflow_id,
        "name": s.name,
        "key": s.key,
        "description": s.description,
        "position": s.position,
        "color": s.color,
        "state_type": s.state_type,
        "is_initial": s.is_initial,
        "is_terminal": s.is_terminal,
        "approval_config": s.approval_config,
        "available_actions": (s.approval_config or {}).get("available_actions"),
        "incoming_count": sum(1 for t in transitions if t.to_state_id == s.id),
        "outgoing_count": sum(1 for t in transitions if t.from_state_id == s.id),
    }


def _transition_out(t: WorkflowTransition) -> Dict[str, Any]:
    return {
        "id": t.id,
        "workflow_id": t.workflow_id,
        "name": t.name,
        "from_state_id": t.from_state_id,
        "to_state_id": t.to_state_id,
        "description": t.description,
        "position": t.position,
        "requires_approval": t.requires_approval,
        "approval_config": t.approval_config,
        "conditions": [
            {
                "id": c.id, "field": c.field, "operator": c.operator, "value": c.value,
                "condition_type": c.condition_type, "configuration": c.configuration,
            } for c in (t.conditions or [])
        ],
        "actions": [
            {
                "id": a.id, "action_type": a.action_type, "configuration": a.configuration,
                "position": a.position, "enabled": (a.configuration or {}).get("enabled", True) is not False,
            } for a in (t.actions or [])
        ],
    }


def _write_audit(db: Session, workflow: Workflow, user: User, event_type: str,
                 metadata: Optional[Dict[str, Any]] = None, entity_id: Optional[UUID] = None):
    record_event(
        db=db,
        organization_id=workflow.organization_id,
        event_type=event_type,
        entity_type="WORKFLOW",
        actor_user_id=user.id,
        entity_id=entity_id or workflow.id,
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# Phase 29 endpoints (unchanged behavior, tenant isolation preserved)
# ---------------------------------------------------------------------------

@router.get("", response_model=List[WorkflowResponse])
def get_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    return db.query(Workflow).filter(Workflow.organization_id == org_id).all()


@router.post("", response_model=WorkflowResponse, status_code=201)
def create_workflow(
    workflow_in: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.create")

    workflow = Workflow(
        organization_id=org_id,
        name=workflow_in.name,
        description=workflow_in.description,
        entity_type=workflow_in.entity_type,
        is_active=workflow_in.is_active,
        created_by=current_user.id
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    for s in workflow_in.states:
        state = WorkflowState(workflow_id=workflow.id, **s.model_dump())
        db.add(state)

    for t in workflow_in.transitions:
        trans = WorkflowTransition(workflow_id=workflow.id, **t.model_dump())
        db.add(trans)

    db.commit()
    db.refresh(workflow)

    _write_audit(db, workflow, current_user, "workflow.created", {"name": workflow.name})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(workflow.id)})
    return workflow


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    return wf


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: UUID,
    workflow_in: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    update_data = workflow_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wf, field, value)
    db.commit()
    db.refresh(wf)
    _write_audit(db, wf, current_user, "workflow.updated", {"changes": update_data})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return wf


@router.delete("/{workflow_id}", status_code=204)
def delete_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.delete")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    db.delete(wf)
    db.commit()
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(workflow_id), "deleted": True})
    return None


@router.post("/{workflow_id}/transitions/{transition_id}/execute")
def execute_transition(
    workflow_id: UUID,
    transition_id: UUID,
    request: TransitionExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.execute")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    trans = db.query(WorkflowTransition).filter(
        WorkflowTransition.id == transition_id, WorkflowTransition.workflow_id == workflow_id
    ).first()
    if not trans:
        raise HTTPException(status_code=404, detail="Transition not found")

    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow_id,
        WorkflowExecution.entity_id == request.entity_id,
        WorkflowExecution.status == "ACTIVE",
    ).order_by(WorkflowExecution.started_at.desc()).first()
    if not execution:
        raise HTTPException(status_code=404, detail="No active execution for this entity")

    result = studio.apply_transition(db, wf, execution, trans, current_user.id, request.context)
    return {"status": result.get("status"), "detail": result}


# ---------------------------------------------------------------------------
# Phase 30 — Visual studio endpoints
# ---------------------------------------------------------------------------

@router.get("/{workflow_id}/studio", response_model=StudioGraph)
def get_studio(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    wf = _get_workflow_or_404(db, workflow_id, org_id)

    layouts = db.query(WorkflowStateLayout).filter(WorkflowStateLayout.workflow_id == wf.id).all()
    forms = db.query(WorkflowForm).filter(WorkflowForm.workflow_id == wf.id).all()
    versions = db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == wf.id
    ).order_by(WorkflowVersion.version_number.desc()).all()
    published = next((v for v in versions if v.status == WorkflowVersionStatus.PUBLISHED), None)

    return StudioGraph(
        workflow=WorkflowResponse.model_validate(wf),
        states=[StateStudioResponse(**_state_out(s)) for s in wf.states],
        transitions=[TransitionStudioResponse(**_transition_out(t)) for t in wf.transitions],
        layouts=[StateLayoutResponse(state_id=l.state_id, x=l.x, y=l.y) for l in layouts],
        forms=[{"id": f.id, "name": f.name, "is_active": f.is_active, "field_count": len((f.configuration or {}).get("fields", []))} for f in forms],
        versions=[WorkflowVersionResponse.model_validate(v) for v in versions],
        published_version_number=published.version_number if published else None,
        validation=ValidationResult(**studio.validate_workflow(db, wf)),
    )


@router.post("/{workflow_id}/states", response_model=StateStudioResponse, status_code=201)
def create_state(
    workflow_id: UUID,
    state_in: StateStudioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)

    key = state_in.key or studio.generate_state_key(state_in.name)
    existing = db.query(WorkflowState).filter(WorkflowState.workflow_id == wf.id, WorkflowState.key == key).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"State key \"{key}\" already exists in this workflow")

    if state_in.is_initial:
        for s in db.query(WorkflowState).filter(WorkflowState.workflow_id == wf.id, WorkflowState.is_initial == True).all():
            s.is_initial = False
            s.state_type = WorkflowStateType.NORMAL.value if s.state_type == WorkflowStateType.INITIAL.value else s.state_type
            db.add(s)

    approval_dict = state_in.approval_config.model_dump(exclude_none=True) if state_in.approval_config else None
    if approval_dict is not None and state_in.approval_config:
        approval_dict["available_actions"] = state_in.available_actions

    state = WorkflowState(
        workflow_id=wf.id,
        name=state_in.name,
        key=key,
        description=state_in.description,
        position=state_in.position,
        color=state_in.color,
        state_type=state_in.state_type.value,
        is_initial=state_in.is_initial,
        is_terminal=state_in.is_terminal,
        approval_config=approval_dict,
    )
    studio.sync_state_flags(state)
    db.add(state)
    db.commit()
    db.refresh(state)

    _write_audit(db, wf, current_user, "workflow.state_created", {"state": state.name, "key": state.key})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return StateStudioResponse(**_state_out(state))


@router.patch("/{workflow_id}/states/{state_id}", response_model=StateStudioResponse)
def update_state(
    workflow_id: UUID,
    state_id: UUID,
    state_in: StateStudioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    state = db.query(WorkflowState).filter(WorkflowState.id == state_id, WorkflowState.workflow_id == wf.id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")

    data = state_in.model_dump(exclude_unset=True)
    approval_cfg = data.pop("approval_config", None)
    available_actions = data.pop("available_actions", None)

    if data.get("is_initial"):
        for s in db.query(WorkflowState).filter(WorkflowState.workflow_id == wf.id, WorkflowState.is_initial == True, WorkflowState.id != state.id).all():
            s.is_initial = False
            s.state_type = WorkflowStateType.NORMAL.value if s.state_type == WorkflowStateType.INITIAL.value else s.state_type
            db.add(s)

    for field, value in data.items():
        setattr(state, field, value)

    if approval_cfg is not None:
        merged = dict(state.approval_config or {})
        merged.update(approval_cfg)
        state.approval_config = merged
    if available_actions is not None:
        merged = dict(state.approval_config or {})
        merged["available_actions"] = available_actions
        state.approval_config = merged

    studio.sync_state_flags(state)
    db.commit()
    db.refresh(state)

    _write_audit(db, wf, current_user, "workflow.state_updated", {"state": state.name, "changes": data})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return StateStudioResponse(**_state_out(state))


@router.delete("/{workflow_id}/states/{state_id}", status_code=204)
def delete_state(
    workflow_id: UUID,
    state_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    state = db.query(WorkflowState).filter(WorkflowState.id == state_id, WorkflowState.workflow_id == wf.id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    name = state.name
    db.delete(state)
    db.commit()
    _write_audit(db, wf, current_user, "workflow.state_deleted", {"state": name})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return None


@router.post("/{workflow_id}/transitions", response_model=TransitionStudioResponse, status_code=201)
def create_transition(
    workflow_id: UUID,
    transition_in: TransitionStudioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)

    from_state = db.query(WorkflowState).filter(WorkflowState.id == transition_in.from_state_id, WorkflowState.workflow_id == wf.id).first()
    to_state = db.query(WorkflowState).filter(WorkflowState.id == transition_in.to_state_id, WorkflowState.workflow_id == wf.id).first()
    if not from_state or not to_state:
        raise HTTPException(status_code=400, detail="Invalid transition: from/to states must belong to this workflow")
    if transition_in.from_state_id == transition_in.to_state_id:
        raise HTTPException(status_code=400, detail="Invalid transition: cannot connect a state to itself")

    transition = WorkflowTransition(
        workflow_id=wf.id,
        name=transition_in.name,
        from_state_id=transition_in.from_state_id,
        to_state_id=transition_in.to_state_id,
        description=transition_in.description,
        requires_approval=transition_in.requires_approval,
        approval_config=transition_in.approval_config.model_dump(exclude_none=True) if transition_in.approval_config else None,
    )
    db.add(transition)
    db.flush()

    for c in transition_in.conditions:
        db.add(WorkflowCondition(
            transition_id=transition.id,
            condition_type=c.condition_type,
            field=c.field,
            operator=c.operator,
            value=c.value,
        ))
    for a in transition_in.actions:
        cfg = {**(a.configuration or {}), "enabled": a.enabled}
        db.add(WorkflowAction(
            transition_id=transition.id,
            action_type=a.action_type,
            configuration=cfg,
            position=a.position,
        ))

    db.commit()
    db.refresh(transition)

    _write_audit(db, wf, current_user, "workflow.transition_created",
                 {"transition": transition.name, "from": from_state.name, "to": to_state.name})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return TransitionStudioResponse(**_transition_out(transition))


@router.patch("/{workflow_id}/transitions/{transition_id}", response_model=TransitionStudioResponse)
def update_transition(
    workflow_id: UUID,
    transition_id: UUID,
    transition_in: TransitionStudioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    transition = db.query(WorkflowTransition).filter(
        WorkflowTransition.id == transition_id, WorkflowTransition.workflow_id == wf.id
    ).first()
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")

    data = transition_in.model_dump(exclude_unset=True)
    conditions = data.pop("conditions", None)
    actions = data.pop("actions", None)
    approval_cfg = data.pop("approval_config", None)

    for field, value in data.items():
        setattr(transition, field, value)

    if approval_cfg is not None:
        transition.approval_config = approval_cfg

    if conditions is not None:
        transition.conditions.clear()
        db.flush()
        for c in conditions:
            c = ConditionSchema.model_validate(c)
            db.add(WorkflowCondition(
                transition_id=transition.id,
                condition_type=c.condition_type,
                field=c.field,
                operator=c.operator,
                value=c.value,
            ))
    if actions is not None:
        transition.actions.clear()
        db.flush()
        for idx, a in enumerate(actions):
            a = ActionSchema.model_validate(a)
            cfg = {**(a.configuration or {}), "enabled": a.enabled}
            db.add(WorkflowAction(
                transition_id=transition.id,
                action_type=a.action_type,
                configuration=cfg,
                position=a.position if a.position else idx,
            ))

    db.commit()
    db.refresh(transition)

    _write_audit(db, wf, current_user, "workflow.transition_updated", {"transition": transition.name})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return TransitionStudioResponse(**_transition_out(transition))


@router.delete("/{workflow_id}/transitions/{transition_id}", status_code=204)
def delete_transition(
    workflow_id: UUID,
    transition_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    transition = db.query(WorkflowTransition).filter(
        WorkflowTransition.id == transition_id, WorkflowTransition.workflow_id == wf.id
    ).first()
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")
    name = transition.name
    db.delete(transition)
    db.commit()
    _write_audit(db, wf, current_user, "workflow.transition_deleted", {"transition": name})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return None


@router.post("/{workflow_id}/layout", response_model=List[StateLayoutResponse])
def save_layout(
    workflow_id: UUID,
    request: LayoutSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)

    state_ids = {s.id for s in wf.states}
    existing = {l.state_id: l for l in db.query(WorkflowStateLayout).filter(WorkflowStateLayout.workflow_id == wf.id).all()}
    saved = []
    for pos in request.positions:
        if pos.state_id not in state_ids:
            continue
        layout = existing.get(pos.state_id)
        if layout:
            layout.x = pos.x
            layout.y = pos.y
        else:
            layout = WorkflowStateLayout(workflow_id=wf.id, state_id=pos.state_id, x=pos.x, y=pos.y)
            db.add(layout)
        saved.append(layout)
    db.commit()
    for l in saved:
        db.refresh(l)
    _write_audit(db, wf, current_user, "workflow.layout_saved", {"count": len(saved)})
    return [StateLayoutResponse(state_id=l.state_id, x=l.x, y=l.y) for l in saved]


@router.post("/{workflow_id}/layout/reset", response_model=List[StateLayoutResponse])
def reset_layout(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    db.query(WorkflowStateLayout).filter(WorkflowStateLayout.workflow_id == wf.id).delete()

    saved = []
    for idx, s in enumerate(sorted(wf.states, key=lambda x: (x.position, x.created_at if hasattr(x, "created_at") else 0))):
        layout = WorkflowStateLayout(workflow_id=wf.id, state_id=s.id, x=120.0 + (idx % 3) * 260.0, y=100.0 + (idx // 3) * 160.0)
        db.add(layout)
        saved.append(layout)
    db.commit()
    for l in saved:
        db.refresh(l)
    _write_audit(db, wf, current_user, "workflow.layout_reset", {})
    return [StateLayoutResponse(state_id=l.state_id, x=l.x, y=l.y) for l in saved]


# ---------------------------------------------------------------------------
# Phase 30 — Validation
# ---------------------------------------------------------------------------

@router.post("/{workflow_id}/validate", response_model=ValidationResult)
def validate(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    return ValidationResult(**studio.validate_workflow(db, wf))


# ---------------------------------------------------------------------------
# Phase 30 — Simulation (dry-run only)
# ---------------------------------------------------------------------------

@router.post("/{workflow_id}/simulate", response_model=SimulationResponse)
def simulate(
    workflow_id: UUID,
    request: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.simulate")
    wf = _get_workflow_or_404(db, workflow_id, org_id)

    result = studio.simulate_workflow(
        db, wf,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        sample_data=request.sample_data,
        start_state_id=request.start_state_id,
        target_state_id=request.target_state_id,
    )
    _write_audit(db, wf, current_user, "workflow.simulation_started",
                 {"entity_type": request.entity_type, "dry_run": True})
    return SimulationResponse(**result)


# ---------------------------------------------------------------------------
# Phase 30 — Versioning
# ---------------------------------------------------------------------------

@router.get("/{workflow_id}/versions", response_model=List[WorkflowVersionResponse])
def list_versions(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    return db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == wf.id
    ).order_by(WorkflowVersion.version_number.desc()).all()


@router.post("/{workflow_id}/versions", response_model=WorkflowVersionResponse, status_code=201)
def create_version(
    workflow_id: UUID,
    request: VersionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.update")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    version = studio.create_version(db, wf, current_user.id, request.change_note)
    _write_audit(db, wf, current_user, "workflow.version_created",
                 {"version_number": version.version_number, "change_note": request.change_note})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return version


@router.get("/{workflow_id}/versions/{version_id}", response_model=WorkflowVersionDetail)
def get_version(
    workflow_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    version = db.query(WorkflowVersion).filter(
        WorkflowVersion.id == version_id, WorkflowVersion.workflow_id == wf.id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return WorkflowVersionDetail(
        **WorkflowVersionResponse.model_validate(version).model_dump(),
        snapshot=version.snapshot,
    )


@router.post("/{workflow_id}/publish", response_model=Dict[str, Any])
def publish_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.publish")
    wf = _get_workflow_or_404(db, workflow_id, org_id)

    # Prefer the latest draft version; otherwise snapshot the live graph into a new version.
    version = db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == wf.id,
        WorkflowVersion.status == WorkflowVersionStatus.DRAFT,
    ).order_by(WorkflowVersion.version_number.desc()).first()
    if not version:
        version = studio.create_version(db, wf, current_user.id, change_note="Published from studio")

    result = studio.publish_version(db, wf, version, current_user.id)
    if result.get("validation_failed"):
        raise HTTPException(status_code=400, detail={
            "message": "Workflow validation failed — publishing blocked",
            "validation": ValidationResult(**result["validation"]).model_dump(mode="json"),
        })

    _write_audit(db, wf, current_user, "workflow.published", {"version_number": version.version_number})
    studio.broadcast_workflow_event(org_id, "workflow.published", {
        "workflow_id": str(wf.id), "version_number": version.version_number,
    })
    return {
        "status": "published",
        "version": WorkflowVersionResponse.model_validate(version).model_dump(mode="json"),
        "validation": result.get("validation"),
    }


@router.post("/{workflow_id}/archive", response_model=Dict[str, Any])
def archive_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.publish")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    now = datetime.now(timezone.utc)

    published = db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == wf.id,
        WorkflowVersion.status == WorkflowVersionStatus.PUBLISHED,
    ).all()
    for v in published:
        v.status = WorkflowVersionStatus.ARCHIVED
        v.archived_at = now
        db.add(v)

    wf.is_active = False
    db.commit()
    _write_audit(db, wf, current_user, "workflow.archived", {"archived_versions": len(published)})
    studio.broadcast_workflow_event(org_id, "workflow.archived", {"workflow_id": str(wf.id)})
    return {"status": "archived", "archived_versions": len(published)}


# ---------------------------------------------------------------------------
# Phase 30 — Executions
# ---------------------------------------------------------------------------

@router.get("/{workflow_id}/executions", response_model=List[ExecutionResponse])
def list_executions(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    executions = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == wf.id
    ).order_by(WorkflowExecution.started_at.desc()).limit(100).all()
    out = []
    for e in executions:
        item = ExecutionResponse.model_validate(e)
        if e.started_at and e.completed_at:
            item.duration_seconds = (e.completed_at - e.started_at).total_seconds()
        out.append(item)
    return out


@router.get("/{workflow_id}/executions/{execution_id}", response_model=ExecutionDetail)
def get_execution(
    workflow_id: UUID,
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    e = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == execution_id, WorkflowExecution.workflow_id == wf.id
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Execution not found")
    detail = ExecutionDetail.model_validate(e)
    if e.started_at and e.completed_at:
        detail.duration_seconds = (e.completed_at - e.started_at).total_seconds()
    detail.events = [
        ExecutionEventResponse(
            id=ev.id, event_type=ev.event_type,
            from_state_id=ev.from_state_id, to_state_id=ev.to_state_id,
            actor_user_id=ev.actor_user_id, metadata=ev.metadata_,
            created_at=ev.created_at,
        ) for ev in (e.events or [])
    ]
    return detail


@router.post("/{workflow_id}/executions", response_model=ExecutionDetail, status_code=201)
def start_execution(
    workflow_id: UUID,
    request: ExecutionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.execute")
    wf = _get_workflow_or_404(db, workflow_id, org_id)

    # Tenant isolation: the entity must exist inside this organization.
    entity = None
    if request.entity_type == "TASK":
        entity = db.query(Task).join(Task.project).filter(
            Task.id == request.entity_id, Task.project.has(organization_id=org_id)
        ).first()
    if request.entity_type == "TASK" and not entity:
        raise HTTPException(status_code=404, detail="Entity not found in this organization")

    execution = studio.start_execution(db, wf, request.entity_type, request.entity_id,
                                       current_user.id, request.trigger_source or "MANUAL")
    detail = ExecutionDetail.model_validate(execution)
    detail.events = list(execution.events)
    return detail


# ---------------------------------------------------------------------------
# Phase 30 — Forms
# ---------------------------------------------------------------------------

@router.get("/{workflow_id}/forms", response_model=List[FormResponse])
def list_forms(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    return db.query(WorkflowForm).filter(WorkflowForm.workflow_id == wf.id).all()


@router.post("/{workflow_id}/forms", response_model=FormResponse, status_code=201)
def create_form(
    workflow_id: UUID,
    form_in: FormCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.manage_forms")
    wf = _get_workflow_or_404(db, workflow_id, org_id)

    fields = [f.model_dump(mode="json") for f in form_in.fields]
    issues = studio.validate_form_config(fields)
    blocking = [i for i in issues if i["severity"] == "ERROR"]
    if blocking:
        raise HTTPException(status_code=400, detail={"message": "Form configuration invalid", "issues": blocking})

    form = WorkflowForm(
        organization_id=org_id,
        workflow_id=wf.id,
        name=form_in.name,
        description=form_in.description,
        is_active=form_in.is_active,
        configuration={"fields": fields},
    )
    db.add(form)
    db.commit()
    db.refresh(form)
    _write_audit(db, wf, current_user, "workflow.form_created", {"form": form.name})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return form


@router.patch("/{workflow_id}/forms/{form_id}", response_model=FormResponse)
def update_form(
    workflow_id: UUID,
    form_id: UUID,
    form_in: FormUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.manage_forms")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    form = db.query(WorkflowForm).filter(
        WorkflowForm.id == form_id, WorkflowForm.workflow_id == wf.id,
        WorkflowForm.organization_id == org_id,
    ).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    data = form_in.model_dump(exclude_unset=True)
    fields = data.pop("fields", None)
    if fields is not None:
        field_dicts = [
            f if isinstance(f, dict) else f.model_dump(mode="json") for f in fields
        ]
        issues = studio.validate_form_config(field_dicts)
        blocking = [i for i in issues if i["severity"] == "ERROR"]
        if blocking:
            raise HTTPException(status_code=400, detail={"message": "Form configuration invalid", "issues": blocking})
        config = dict(form.configuration or {})
        config["fields"] = field_dicts
        form.configuration = config
    for field, value in data.items():
        setattr(form, field, value)
    db.commit()
    db.refresh(form)
    _write_audit(db, wf, current_user, "workflow.form_updated", {"form": form.name})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(wf.id)})
    return form


@router.delete("/{workflow_id}/forms/{form_id}", status_code=204)
def delete_form(
    workflow_id: UUID,
    form_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.manage_forms")
    wf = _get_workflow_or_404(db, workflow_id, org_id)
    form = db.query(WorkflowForm).filter(
        WorkflowForm.id == form_id, WorkflowForm.workflow_id == wf.id,
        WorkflowForm.organization_id == org_id,
    ).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    db.delete(form)
    db.commit()
    _write_audit(db, wf, current_user, "workflow.form_deleted", {"form": form.name})
    return None


# ---------------------------------------------------------------------------
# Phase 30 — AI assistant apply (explicit, user-driven, advisory only)
# ---------------------------------------------------------------------------

@router.post("/ai/apply", response_model=WorkflowResponse, status_code=201)
def apply_ai_suggestion(
    request: AIApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    """Apply a REVIEWED AI suggestion as a new DRAFT workflow.

    This is an explicit user action — the AI itself never saves anything.
    The resulting workflow starts in draft and must still pass validation
    before it can be published.
    """
    get_workflow_permission(db, current_user, org_id, "workflows.create")

    s = request.suggestion
    try:
        entity_type = WorkflowEntityType(s.entity_type)
    except ValueError:
        entity_type = WorkflowEntityType.TASK

    workflow = Workflow(
        organization_id=org_id,
        name=s.name or "AI Suggested Workflow",
        description=s.description,
        entity_type=entity_type,
        is_active=False,  # draft until explicitly published
        created_by=current_user.id,
    )
    db.add(workflow)
    db.flush()

    key_to_state = {}
    for idx, sd in enumerate(s.states):
        key = (sd.get("key") or studio.generate_state_key(sd.get("name", f"STATE{idx}")))
        state_type = sd.get("state_type") or "NORMAL"
        try:
            WorkflowStateType(state_type)
        except ValueError:
            state_type = WorkflowStateType.NORMAL.value
        state = WorkflowState(
            workflow_id=workflow.id,
            name=sd.get("name") or key,
            key=key,
            description=sd.get("description"),
            position=sd.get("position", idx),
            color=sd.get("color"),
            state_type=state_type,
            is_initial=bool(sd.get("is_initial")),
            is_terminal=bool(sd.get("is_terminal")),
            approval_config=sd.get("approval_config"),
        )
        studio.sync_state_flags(state)
        db.add(state)
        key_to_state[key] = state
    db.flush()

    for idx, td in enumerate(s.transitions):
        from_state = key_to_state.get(td.get("from_key"))
        to_state = key_to_state.get(td.get("to_key"))
        if not from_state or not to_state:
            continue
        transition = WorkflowTransition(
            workflow_id=workflow.id,
            name=td.get("name") or f"Transition {idx + 1}",
            from_state_id=from_state.id,
            to_state_id=to_state.id,
            description=td.get("description"),
            requires_approval=bool(td.get("requires_approval")),
            approval_config=td.get("approval_config"),
            position=idx,
        )
        db.add(transition)
        db.flush()
        for c in (td.get("conditions") or []):
            operator = c.get("operator")
            if operator not in SAFE_OPERATORS:
                continue  # never persist unsafe conditions
            db.add(WorkflowCondition(
                transition_id=transition.id,
                condition_type=WorkflowConditionType.FIELD_EQUALS,
                field=c.get("field"),
                operator=operator,
                value=str(c.get("value")) if c.get("value") is not None else None,
            ))
        for ad in (td.get("actions") or []):
            try:
                action_type = WorkflowActionType(ad.get("action_type"))
            except (ValueError, TypeError):
                continue  # never persist unknown action types
            db.add(WorkflowAction(
                transition_id=transition.id,
                action_type=action_type,
                configuration=ad.get("configuration") or {},
                position=ad.get("position", 0),
            ))

    if s.form_fields:
        field_dicts = []
        for idx, f in enumerate(s.form_fields):
            fd = dict(f)
            fd.setdefault("id", f"field_{idx}")
            fd.setdefault("position", idx)
            field_dicts.append(fd)
        issues = studio.validate_form_config(field_dicts)
        if not [i for i in issues if i["severity"] == "ERROR"]:
            db.add(WorkflowForm(
                organization_id=org_id,
                workflow_id=workflow.id,
                name="AI Suggested Form",
                description="Generated by the AI workflow assistant (reviewed draft)",
                is_active=True,
                configuration={"fields": field_dicts},
            ))

    db.commit()
    db.refresh(workflow)

    _write_audit(db, workflow, current_user, "workflow.created",
                 {"name": workflow.name, "source": "ai_suggestion_applied", "preview_only": False})
    studio.broadcast_workflow_event(org_id, "workflow.updated", {"workflow_id": str(workflow.id)})
    return workflow


# ---------------------------------------------------------------------------
# Phase 30 — Analytics
# ---------------------------------------------------------------------------

@router.get("/{workflow_id}/analytics", response_model=WorkflowAnalyticsResponse)
def workflow_analytics(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    get_workflow_permission(db, current_user, org_id, "workflows.view")
    wf = _get_workflow_or_404(db, workflow_id, org_id)

    executions = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == wf.id).all()
    total = len(executions)
    successful = sum(1 for e in executions if e.status == "COMPLETED")
    failed = sum(1 for e in executions if e.status == "FAILED")
    active = sum(1 for e in executions if e.status == "ACTIVE")
    durations = [
        (e.completed_at - e.started_at).total_seconds()
        for e in executions if e.completed_at and e.started_at
    ]

    from sqlalchemy import func
    approval_total = db.query(func.count(WorkflowApproval.id)).join(WorkflowTransition).filter(
        WorkflowTransition.workflow_id == wf.id
    ).scalar() or 0
    approval_rejected = db.query(func.count(WorkflowApproval.id)).join(WorkflowTransition).filter(
        WorkflowTransition.workflow_id == wf.id, WorkflowApproval.status == "REJECTED"
    ).scalar() or 0

    # State duration: average time spent per state from TRANSITION events
    state_durations: Dict[str, Any] = {}
    for e in executions:
        events = [ev for ev in (e.events or [])]
        for ev in events:
            if ev.event_type == "TRANSITION" and ev.from_state_id:
                state = db.query(WorkflowState).filter(WorkflowState.id == ev.from_state_id).first()
                if state:
                    entry = state_durations.setdefault(state.name, {"state": state.name, "avg_seconds": 0.0, "count": 0})
                    entry["count"] += 1

    from collections import Counter
    transition_counts = Counter()
    for e in executions:
        for ev in (e.events or []):
            if ev.event_type == "TRANSITION":
                name = ((ev.metadata_ or {}).get("transition")) or "unknown"
                transition_counts[name] += 1

    most_used_transition = None
    if transition_counts:
        t_name, t_count = transition_counts.most_common(1)[0]
        most_used_transition = {"name": t_name, "count": t_count}

    return WorkflowAnalyticsResponse(
        total_workflows=1,
        published_workflows=1 if db.query(WorkflowVersion).filter(
            WorkflowVersion.workflow_id == wf.id,
            WorkflowVersion.status == WorkflowVersionStatus.PUBLISHED,
        ).count() else 0,
        draft_workflows=db.query(WorkflowVersion).filter(
            WorkflowVersion.workflow_id == wf.id,
            WorkflowVersion.status == WorkflowVersionStatus.DRAFT,
        ).count(),
        total_executions=total,
        successful_executions=successful,
        failed_executions=failed,
        active_executions=active,
        avg_execution_seconds=(sum(durations) / len(durations)) if durations else None,
        failure_rate=(failed / total) if total else None,
        approval_rejection_rate=(approval_rejected / approval_total) if approval_total else None,
        most_used_transition=most_used_transition,
        state_durations=list(state_durations.values()),
    )
