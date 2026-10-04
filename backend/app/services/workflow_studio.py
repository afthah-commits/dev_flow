"""Phase 30 — Visual Workflow Studio service.

Central business logic for the visual workflow studio:
- Workflow graph validation (publish gate)
- Dry-run simulation (never touches production data)
- Versioning (draft / published / archived lifecycle)
- Execution engine (start + apply transition with approval gate)
- Form configuration validation (safe conditional fields)

Everything here reuses existing Phase 29 infrastructure:
- Safe condition evaluation reuses app.services.automation_engine (no eval())
- SEND_NOTIFICATION reuses app.services.notification_service
- Audit logging reuses app.services.audit_service.record_event
- Realtime reuses app.websockets.manager (Phase 23/24)
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.workflow import (
    Workflow,
    WorkflowState,
    WorkflowStateType,
    WorkflowTransition,
    WorkflowCondition,
    WorkflowAction,
    WorkflowActionType,
    WorkflowApproval,
    WorkflowExecution,
    WorkflowExecutionEvent,
    WorkflowVersion,
    WorkflowVersionStatus,
    WorkflowForm,
)
from app.models.task import Task
from app.services.automation_engine import evaluate_condition, evaluate_condition_group
from app.services.audit_service import record_event
from app.schemas.workflow import SAFE_OPERATORS, FORM_FIELD_TYPES

# Maximum simulated steps to guarantee termination on cyclic graphs
MAX_SIMULATION_STEPS = 50


# ---------------------------------------------------------------------------
# Realtime (Phase 23/24 integration)
# ---------------------------------------------------------------------------

def broadcast_workflow_event(org_id, event_type: str, payload: Dict[str, Any]) -> None:
    """Broadcast a workflow.* realtime event to all organization sockets.

    Safe to call from sync endpoints: reuses the existing websocket manager
    without blocking the request thread.
    """
    message = {
        "type": event_type,
        "entity": "workflow",
        "payload": payload,
    }
    try:
        manager_module = __import__("app.websockets.manager", fromlist=["manager"])
        manager = manager_module.manager
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(manager.broadcast_to_org(org_id, message), loop)
                return
        except RuntimeError:
            pass
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(manager.broadcast_to_org(org_id, message))
        finally:
            loop.close()
    except Exception:
        # Realtime must never break the request pipeline
        pass


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def generate_state_key(name: str) -> str:
    key = "".join(ch for ch in name.upper() if ch.isalnum())
    return key or "STATE"


def sync_state_flags(state: WorkflowState) -> None:
    """Keep the Phase 29 booleans in sync with the Phase 30 state_type."""
    if state.state_type == WorkflowStateType.INITIAL.value:
        state.is_initial = True
    elif state.state_type in (
        WorkflowStateType.COMPLETED.value,
        WorkflowStateType.FAILED.value,
        WorkflowStateType.CANCELLED.value,
    ):
        state.is_terminal = True


def get_entity_data(db: Session, org_id: UUID, entity_type: str, entity_id: Optional[UUID]) -> Dict[str, Any]:
    """Read-only projection of an entity for condition evaluation."""
    if not entity_id:
        return {}
    if entity_type == "TASK":
        task = db.query(Task).filter(Task.id == entity_id).first()
        if task:
            project = None
            try:
                from app.models.project import Project
                project = db.query(Project).filter(
                    Project.id == task.project_id, Project.organization_id == org_id
                ).first()
            except Exception:
                pass
            if project is None:
                return {}
            return {
                "id": str(task.id),
                "task_key": task.task_key,
                "title": task.title,
                "status": task.status.value if hasattr(task.status, "value") else str(task.status),
                "priority": task.priority.value if hasattr(task.priority, "value") else str(task.priority),
                "estimate_points": task.estimate_points,
                "estimate_hours": task.estimate_hours,
                "is_blocked": task.is_blocked,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "assignee_id": str(task.assignee_id) if task.assignee_id else None,
                "project_id": str(task.project_id),
            }
    return {}


def _condition_payload(transition: WorkflowTransition) -> Tuple[List[WorkflowCondition], str]:
    conditions = list(transition.conditions or [])
    logical = "ALL"
    if conditions:
        config = conditions[0].configuration or {}
        logical = config.get("logical_operator") or conditions[0].condition_type.value \
            if conditions[0].condition_type and conditions[0].condition_type.value in ("ALL", "ANY") \
            else config.get("logical_operator", "ALL")
        if logical not in ("ALL", "ANY", "NOT"):
            logical = "ALL"
    return conditions, logical


def evaluate_transition_conditions(transition: WorkflowTransition, data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    """Evaluate a transition's conditions using the safe Phase 29 engine."""
    conditions, logical = _condition_payload(transition)
    if not conditions:
        return True, []

    evaluations: List[Dict[str, Any]] = []
    group = {
        "logical_operator": logical,
        "conditions": [
            {"field": c.field, "operator": c.operator, "value": c.value}
            for c in conditions
        ],
    }
    result = evaluate_condition_group(group, data)
    for c in conditions:
        single = {"field": c.field, "operator": c.operator, "value": c.value}
        evaluations.append({
            "field": c.field,
            "operator": c.operator,
            "value": c.value,
            "result": evaluate_condition(single, data),
        })
    return bool(result), evaluations


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_workflow(db: Session, workflow: Workflow) -> Dict[str, Any]:
    """Validate the workflow graph. Returns a ValidationResult-shaped dict."""
    issues: List[Dict[str, Any]] = []
    states = list(workflow.states or [])
    transitions = list(workflow.transitions or [])
    state_ids = {s.id for s in states}
    state_by_id = {s.id: s for s in states}

    def issue(severity: str, code: str, message: str, entity: Optional[Any] = None):
        issues.append({
            "severity": severity,
            "code": code,
            "message": message,
            "entity_type": type(entity).__name__ if entity else None,
            "entity_id": entity.id if entity is not None and isinstance(getattr(entity, "id", None), UUID) else None,
            "entity_name": getattr(entity, "name", None) if entity is not None else None,
        })

    # --- Initial / final states ---
    initial_states = [s for s in states if s.is_initial]
    final_states = [s for s in states if s.is_terminal]

    if not states:
        issue("ERROR", "NO_STATES", "Workflow has no states configured")
    else:
        if len(initial_states) == 1:
            issue("PASS", "INITIAL_STATE", f"Initial state configured: \"{initial_states[0].name}\"")
        elif len(initial_states) == 0:
            issue("ERROR", "NO_INITIAL_STATE", "No initial state configured")
        else:
            names = ", ".join(f"\"{s.name}\"" for s in initial_states)
            issue("ERROR", "MULTIPLE_INITIAL_STATES", f"Multiple initial states configured: {names}")

        if len(final_states) >= 1:
            issue("PASS", "FINAL_STATE", f"Final state configured: \"{final_states[0].name}\"")
        else:
            issue("ERROR", "NO_FINAL_STATE", "No final (terminal) state configured")

    # --- Duplicate state names / keys ---
    seen_names: Dict[str, WorkflowState] = {}
    seen_keys: Dict[str, WorkflowState] = {}
    for s in states:
        if s.name.lower() in seen_names:
            issue("ERROR", "DUPLICATE_STATE_NAME",
                  f"Duplicate state name: \"{s.name}\"", s)
        seen_names[s.name.lower()] = s
        if s.key in seen_keys:
            issue("ERROR", "DUPLICATE_STATE_KEY", f"Duplicate state key: {s.key}", s)
        seen_keys[s.key] = s

    # --- Transitions ---
    valid_transitions = True
    outgoing: Dict[UUID, List[WorkflowTransition]] = {}
    incoming: Dict[UUID, List[WorkflowTransition]] = {}
    for t in transitions:
        if t.from_state_id not in state_ids or t.to_state_id not in state_ids:
            valid_transitions = False
            issue("ERROR", "BROKEN_TRANSITION",
                  f"Transition \"{t.name}\" references a missing state", t)
            continue
        if t.from_state_id == t.to_state_id:
            valid_transitions = False
            issue("ERROR", "SELF_TRANSITION",
                  f"Transition \"{t.name}\" loops a state onto itself", t)
            continue

        outgoing.setdefault(t.from_state_id, []).append(t)
        incoming.setdefault(t.to_state_id, []).append(t)

        # Conditions
        for c in (t.conditions or []):
            if not c.field and c.condition_type in (
                WorkflowConditionType.FIELD_EQUALS, WorkflowConditionType.FIELD_GREATER
            ):
                valid_transitions = False
                issue("ERROR", "INVALID_CONDITION",
                      f"Transition \"{t.name}\" has a condition without a field", t)
            elif c.field and (c.operator not in SAFE_OPERATORS):
                valid_transitions = False
                issue("ERROR", "INVALID_CONDITION",
                      f"Transition \"{t.name}\" uses unsupported operator \"{c.operator}\"", t)
            elif c.field and c.operator in (
                "GREATER_THAN", "LESS_THAN", "GREATER_THAN_OR_EQUAL", "LESS_THAN_OR_EQUAL"
            ) and c.value in (None, ""):
                valid_transitions = False
                issue("ERROR", "INVALID_CONDITION",
                      f"Transition \"{t.name}\" numeric condition \"{c.field}\" has no comparison value", t)

        # Actions
        for a in (t.actions or []):
            config = a.configuration or {}
            if a.action_type == WorkflowActionType.CREATE_TASK and not (config.get("title") or config.get("title_template")):
                valid_transitions = False
                issue("ERROR", "INVALID_ACTION",
                      f"Transition \"{t.name}\" has invalid action configuration: CREATE_TASK requires a title", t)
            elif a.action_type == WorkflowActionType.SEND_NOTIFICATION and not (config.get("message") or config.get("template")):
                valid_transitions = False
                issue("ERROR", "INVALID_ACTION",
                      f"Transition \"{t.name}\" has invalid action configuration: SEND_NOTIFICATION requires a message", t)
            elif a.action_type == WorkflowActionType.TRIGGER_AUTOMATION and not config.get("automation_id"):
                valid_transitions = False
                issue("ERROR", "INVALID_ACTION",
                      f"Transition \"{t.name}\" has invalid action configuration: TRIGGER_AUTOMATION requires an automation_id", t)
            elif a.action_type == WorkflowActionType.CREATE_AUDIT_EVENT and not config.get("event_type"):
                valid_transitions = False
                issue("ERROR", "INVALID_ACTION",
                      f"Transition \"{t.name}\" has invalid action configuration: CREATE_AUDIT_EVENT requires an event_type", t)

        # Approval configuration
        cfg = t.approval_config or {}
        if t.requires_approval and not cfg.get("required", True):
            issue("WARNING", "MISSING_APPROVAL_CONFIG",
                  f"Transition \"{t.name}\" requires approval but has no approval configuration", t)
        if t.requires_approval and cfg:
            if cfg.get("approver_type") not in (None, "ROLE", "TEAM", "USER"):
                valid_transitions = False
                issue("ERROR", "INVALID_APPROVAL_CONFIG",
                      f"Transition \"{t.name}\" has an invalid approver_type", t)
            if cfg.get("approver_type") == "USER" and not cfg.get("approver_user_id"):
                valid_transitions = False
                issue("ERROR", "INVALID_APPROVAL_CONFIG",
                      f"Transition \"{t.name}\" requires a specific member but none is selected", t)
            if cfg.get("approver_type") == "TEAM" and not cfg.get("team_id"):
                valid_transitions = False
                issue("ERROR", "INVALID_APPROVAL_CONFIG",
                      f"Transition \"{t.name}\" requires a team but none is selected", t)
            if int(cfg.get("minimum_approvals", 1) or 1) < 1:
                valid_transitions = False
                issue("ERROR", "INVALID_APPROVAL_CONFIG",
                      f"Transition \"{t.name}\" has a minimum approval count below 1", t)

    if transitions and valid_transitions:
        issue("PASS", "TRANSITIONS_VALID", "All transitions valid")

    # Missing transition target (self-healing FKs should not allow this, but check anyway)
    for s in states:
        for t in transitions:
            if t.from_state_id == s.id and t.to_state_id not in state_ids:
                issue("ERROR", "MISSING_TRANSITION_TARGET",
                      f"Transition \"{t.name}\" targets a state that no longer exists", t)

    # --- Reachability ---
    if initial_states:
        reachable = set()
        queue = [initial_states[0].id]
        while queue:
            current = queue.pop()
            if current in reachable:
                continue
            reachable.add(current)
            for t in outgoing.get(current, []):
                if t.to_state_id not in reachable:
                    queue.append(t.to_state_id)
        for s in states:
            if s.id not in reachable:
                issue("WARNING", "UNREACHABLE_STATE",
                      f"State \"{s.name}\" is unreachable", s)

    # --- Dead ends ---
    for s in states:
        if not s.is_terminal and not outgoing.get(s.id):
            issue("WARNING", "DEAD_END_STATE",
                  f"State \"{s.name}\" is a dead end: no outgoing transitions and not final", s)

    # --- Circular transition problems (cycles without an exit to a terminal state) ---
    if initial_states and outgoing:
        def reaches_terminal(state_id: UUID, visited: Optional[set] = None) -> bool:
            if visited is None:
                visited = set()
            if state_id in visited:
                return False
            visited.add(state_id)
            state = state_by_id.get(state_id)
            if state and state.is_terminal:
                return True
            for t in outgoing.get(state_id, []):
                if reaches_terminal(t.to_state_id, visited):
                    return True
            return False

        for s in states:
            if s.id in outgoing and not reaches_terminal(s.id):
                issue("WARNING", "CIRCULAR_TRANSITIONS",
                      f"State \"{s.name}\" can loop circularly without reaching a final state", s)

    # --- Missing required form fields ---
    forms = db.query(WorkflowForm).filter(
        WorkflowForm.workflow_id == workflow.id,
        WorkflowForm.is_active == True,
    ).all()
    form_issues = []
    for form in forms:
        config = form.configuration or {}
        fields = config.get("fields", [])
        if not fields:
            form_issues.append(f"Form \"{form.name}\" has no fields configured")
            continue
        for f in fields:
            if not f.get("label"):
                form_issues.append(f"Form \"{form.name}\" has a field missing a label")
            if f.get("type") == "CUSTOM_FIELD" and not f.get("custom_field_id"):
                form_issues.append(f"Form \"{form.name}\" field \"{f.get('label', '?')}\" is a custom field without a linked CustomField")
            vis = f.get("visibility") or {}
            if vis and vis.get("operator") not in SAFE_OPERATORS:
                form_issues.append(
                    f"Form \"{form.name}\" field \"{f.get('label', '?')}\" uses unsupported visibility operator \"{vis.get('operator')}\""
                )
    if form_issues:
        for msg in form_issues:
            issue("ERROR", "FORM_CONFIGURATION", msg)
    elif forms:
        issue("PASS", "FORMS_VALID", "All workflow forms valid")

    has_errors = any(i["severity"] == "ERROR" for i in issues)
    has_warnings = any(i["severity"] == "WARNING" for i in issues)
    status = "ERROR" if has_errors else ("WARNING" if has_warnings else "PASS")

    return {
        "status": status,
        "can_publish": not has_errors,
        "issues": issues,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

def snapshot_workflow(db: Session, workflow: Workflow) -> Dict[str, Any]:
    """Serialize the full workflow definition (graph, layout, forms)."""
    states = []
    for s in workflow.states:
        layout = s.layout[0] if s.layout else None
        states.append({
            "id": str(s.id),
            "name": s.name,
            "key": s.key,
            "description": s.description,
            "position": s.position,
            "color": s.color,
            "state_type": s.state_type,
            "is_initial": s.is_initial,
            "is_terminal": s.is_terminal,
            "approval_config": s.approval_config,
            "layout": {"x": layout.x, "y": layout.y} if layout else {"x": 0, "y": 0},
        })

    transitions = []
    for t in workflow.transitions:
        transitions.append({
            "id": str(t.id),
            "name": t.name,
            "from_state_id": str(t.from_state_id),
            "to_state_id": str(t.to_state_id),
            "position": t.position,
            "requires_approval": t.requires_approval,
            "description": t.description,
            "approval_config": t.approval_config,
            "conditions": [
                {
                    "id": str(c.id),
                    "condition_type": c.condition_type.value if c.condition_type else None,
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value,
                    "configuration": c.configuration,
                }
                for c in (t.conditions or [])
            ],
            "actions": [
                {
                    "id": str(a.id),
                    "action_type": a.action_type.value if a.action_type else None,
                    "configuration": a.configuration,
                    "position": a.position,
                }
                for a in (t.actions or [])
            ],
        })

    forms = db.query(WorkflowForm).filter(WorkflowForm.workflow_id == workflow.id).all()
    return {
        "name": workflow.name,
        "description": workflow.description,
        "entity_type": workflow.entity_type.value if hasattr(workflow.entity_type, "value") else str(workflow.entity_type),
        "is_active": workflow.is_active,
        "states": states,
        "transitions": transitions,
        "forms": [
            {
                "id": str(f.id),
                "name": f.name,
                "description": f.description,
                "is_active": f.is_active,
                "configuration": f.configuration,
            }
            for f in forms
        ],
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def create_version(db: Session, workflow: Workflow, actor_user_id: Optional[UUID],
                   change_note: Optional[str] = None, status: WorkflowVersionStatus = WorkflowVersionStatus.DRAFT) -> WorkflowVersion:
    """Create a new version snapshot of the workflow."""
    latest = db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == workflow.id
    ).order_by(WorkflowVersion.version_number.desc()).first()
    next_number = (latest.version_number + 1) if latest else 1

    now = datetime.now(timezone.utc)
    version = WorkflowVersion(
        organization_id=workflow.organization_id,
        workflow_id=workflow.id,
        version_number=next_number,
        status=status,
        snapshot=snapshot_workflow(db, workflow),
        change_note=change_note,
        created_by=actor_user_id,
        published_at=now if status == WorkflowVersionStatus.PUBLISHED else None,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def publish_version(db: Session, workflow: Workflow, version: WorkflowVersion,
                    actor_user_id: Optional[UUID]) -> Dict[str, Any]:
    """Publish a draft version after running the validation gate."""
    if version.status == WorkflowVersionStatus.PUBLISHED:
        return {"already_published": True, "version": version}
    if version.status == WorkflowVersionStatus.ARCHIVED:
        raise ValueError("Cannot publish an archived version")

    # Validation gate: rebuild the graph from the snapshot and validate it
    validation = validate_published_snapshot(db, workflow.organization_id, version.snapshot)
    if not validation["can_publish"]:
        return {"validation_failed": True, "validation": validation}

    now = datetime.now(timezone.utc)
    # Archive other published versions (published versions remain readable)
    for v in db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == workflow.id,
        WorkflowVersion.status == WorkflowVersionStatus.PUBLISHED,
        WorkflowVersion.id != version.id,
    ).all():
        v.status = WorkflowVersionStatus.ARCHIVED
        v.archived_at = now
        db.add(v)

    version.status = WorkflowVersionStatus.PUBLISHED
    version.published_at = now
    db.add(version)
    db.commit()
    db.refresh(version)
    return {"published": True, "version": version, "validation": validation}


def validate_published_snapshot(db: Session, org_id: UUID, snapshot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate a snapshot without touching the live workflow rows.

    Builds a detached graph in memory and runs the same validators.
    """
    if not snapshot:
        return {"status": "ERROR", "can_publish": False, "issues": [{
            "severity": "ERROR", "code": "EMPTY_SNAPSHOT",
            "message": "Version has no snapshot to validate",
            "entity_type": None, "entity_id": None, "entity_name": None,
        }], "checked_at": datetime.now(timezone.utc).isoformat()}

    proxy = _GraphProxy(org_id, snapshot)
    return validate_workflow(db, proxy)


class _GraphProxy:
    """Lightweight in-memory stand-in for Workflow when validating snapshots."""

    def __init__(self, org_id: UUID, snapshot: Dict[str, Any]):
        from uuid import uuid4
        self.id = uuid4()
        self.organization_id = org_id
        self.name = snapshot.get("name", "")
        self.description = snapshot.get("description")
        from app.models.workflow import WorkflowEntityType
        try:
            self.entity_type = WorkflowEntityType(snapshot.get("entity_type", "TASK"))
        except ValueError:
            self.entity_type = WorkflowEntityType.TASK
        self.is_active = snapshot.get("is_active", True)

        self.states = [
            _StateProxy(s) for s in snapshot.get("states", [])
        ]
        state_id_map = {s["id"]: self.states[i] for i, s in enumerate(snapshot.get("states", []))}
        self.transitions = []
        for t in snapshot.get("transitions", []):
            self.transitions.append(_TransitionProxy(t, state_id_map))


class _StateProxy:
    def __init__(self, data: Dict[str, Any]):
        from uuid import UUID as _UUID
        self.id = _UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id")
        self.name = data.get("name", "")
        self.key = data.get("key", "")
        self.description = data.get("description")
        self.position = data.get("position", 0)
        self.color = data.get("color")
        self.state_type = data.get("state_type") or WorkflowStateType.NORMAL.value
        self.is_initial = bool(data.get("is_initial"))
        self.is_terminal = bool(data.get("is_terminal"))
        self.approval_config = data.get("approval_config")
        self.layout = []


class _TransitionProxy:
    def __init__(self, data: Dict[str, Any], state_id_map: Dict[str, Any]):
        from uuid import UUID as _UUID
        self.id = _UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id")
        self.name = data.get("name", "")
        from_id = data.get("from_state_id")
        to_id = data.get("to_state_id")
        self.from_state_id = state_id_map[from_id].id if from_id in state_id_map else from_id
        self.to_state_id = state_id_map[to_id].id if to_id in state_id_map else to_id
        self.position = data.get("position", 0)
        self.requires_approval = bool(data.get("requires_approval"))
        self.description = data.get("description")
        self.approval_config = data.get("approval_config")
        self.conditions = [_ConditionProxy(c) for c in data.get("conditions", [])]
        self.actions = [_ActionProxy(a) for a in data.get("actions", [])]


class _ConditionProxy:
    def __init__(self, data: Dict[str, Any]):
        self.condition_type = None
        raw = data.get("condition_type")
        if raw:
            try:
                from app.models.workflow import WorkflowConditionType
                self.condition_type = WorkflowConditionType(raw)
            except ValueError:
                self.condition_type = None
        self.field = data.get("field")
        self.operator = data.get("operator")
        self.value = data.get("value")
        self.configuration = data.get("configuration")


class _ActionProxy:
    def __init__(self, data: Dict[str, Any]):
        raw = data.get("action_type")
        try:
            from app.models.workflow import WorkflowActionType
            self.action_type = WorkflowActionType(raw)
        except (ValueError, TypeError):
            self.action_type = None
        self.configuration = data.get("configuration")
        self.position = data.get("position", 0)


# ---------------------------------------------------------------------------
# Execution engine (reuses existing models + services; no duplicate engine)
# ---------------------------------------------------------------------------

def start_execution(db: Session, workflow: Workflow, entity_type: str, entity_id: UUID,
                    actor_user_id: Optional[UUID], trigger_source: str = "MANUAL") -> WorkflowExecution:
    initial = next((s for s in workflow.states if s.is_initial), None)
    published = db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == workflow.id,
        WorkflowVersion.status == WorkflowVersionStatus.PUBLISHED,
    ).order_by(WorkflowVersion.published_at.desc()).first()

    execution = WorkflowExecution(
        workflow_id=workflow.id,
        entity_type=entity_type,
        entity_id=entity_id,
        current_state_id=initial.id if initial else None,
        status="ACTIVE",
        workflow_version_id=published.id if published else None,
        trigger_source=trigger_source,
    )
    db.add(execution)
    db.flush()
    db.add(WorkflowExecutionEvent(
        execution_id=execution.id,
        event_type="STARTED",
        to_state_id=initial.id if initial else None,
        actor_user_id=actor_user_id,
        metadata_={"trigger_source": trigger_source},
    ))
    db.commit()
    db.refresh(execution)

    record_event(
        db=db,
        organization_id=workflow.organization_id,
        event_type="workflow.execution_started",
        entity_type="WORKFLOW",
        actor_user_id=actor_user_id,
        entity_id=execution.id,
        metadata={"workflow_id": str(workflow.id), "entity_type": entity_type, "entity_id": str(entity_id)},
    )
    broadcast_workflow_event(workflow.organization_id, "workflow.execution.started", {
        "workflow_id": str(workflow.id), "execution_id": str(execution.id), "status": execution.status,
    })
    return execution


def execute_workflow_actions(db: Session, workflow: Workflow, execution: WorkflowExecution,
                             transition: WorkflowTransition, actor_user_id: Optional[UUID],
                             data: Dict[str, Any], dry_run: bool = False) -> List[Dict[str, Any]]:
    """Run a transition's actions using existing engine/service logic."""
    results = []
    actions = sorted(transition.actions or [], key=lambda a: a.position or 0)
    for a in actions:
        config = a.configuration or {}
        action_type = a.action_type.value if hasattr(a.action_type, "value") else str(a.action_type)
        result = {"action_type": action_type, "enabled": config.get("enabled", True), "dry_run": dry_run, "status": "SKIPPED"}
        if config.get("enabled") is False:
            results.append(result)
            continue
        if dry_run:
            result["status"] = "WOULD_RUN"
            results.append(result)
            continue
        try:
            if action_type == "CREATE_TASK":
                task = Task(
                    project_id=UUID(config["project_id"]) if config.get("project_id") else None,
                    title=config.get("title") or f"Workflow task from {transition.name}",
                    description=config.get("description"),
                    status=config.get("status", "TODO"),
                    priority=config.get("priority", "MEDIUM"),
                    creator_id=actor_user_id,
                )
                if task.project_id is None:
                    project_id = data.get("project_id")
                    if project_id:
                        from app.models.project import Project
                        project = db.query(Project).filter(
                            Project.id == UUID(str(project_id)), Project.organization_id == workflow.organization_id
                        ).first()
                        if project:
                            task.project_id = project.id
                if task.project_id is None:
                    raise ValueError("CREATE_TASK requires a project (config or entity)")
                db.add(task)
                db.flush()
                result["status"] = "SUCCESS"
                result["task_id"] = str(task.id)
            elif action_type == "UPDATE_TASK":
                entity_id = data.get("id")
                if entity_id and data.get("entity_kind", "TASK") == "TASK":
                    from app.models.task import TaskStatus, TaskPriority
                    task = db.query(Task).filter(Task.id == UUID(str(entity_id))).first()
                    if task:
                        for field in ("status", "priority", "title", "description"):
                            if config.get(field):
                                value = config[field]
                                if field == "status":
                                    value = TaskStatus(value)
                                elif field == "priority":
                                    value = TaskPriority(value)
                                setattr(task, field, value)
                        db.flush()
                        result["status"] = "SUCCESS"
                        result["task_id"] = str(task.id)
                    else:
                        result["status"] = "FAILED"
                        result["error"] = "Task not found"
                else:
                    result["status"] = "SKIPPED"
            elif action_type == "CREATE_COMMENT":
                from app.models.collaboration import Comment
                entity_id = data.get("id")
                if entity_id:
                    comment = Comment(
                        organization_id=workflow.organization_id,
                        author_id=actor_user_id,
                        entity_type=data.get("entity_kind", "TASK"),
                        entity_id=UUID(str(entity_id)),
                        content=config.get("content") or "Workflow comment",
                    )
                    db.add(comment)
                    db.flush()
                    result["status"] = "SUCCESS"
                    result["comment_id"] = str(comment.id)
                else:
                    result["status"] = "SKIPPED"
            elif action_type == "SEND_NOTIFICATION":
                from app.services.notification_service import create_notification
                target = config.get("user_id") or config.get("assignee_user_id")
                user_id = UUID(str(target)) if target else (UUID(str(data.get("assignee_id"))) if data.get("assignee_id") else None)
                if user_id:
                    create_notification(
                        db, user_id,
                        n_type=config.get("notification_type", "SYSTEM"),
                        title=config.get("title") or f"Workflow: {transition.name}",
                        message=config.get("message") or f"Transition {transition.name} executed",
                        project_id=UUID(str(data["project_id"])) if data.get("project_id") else None,
                        priority=config.get("priority", "NORMAL"),
                        entity_type="TASK" if data.get("entity_kind", "TASK") == "TASK" else data.get("entity_kind"),
                        entity_id=UUID(str(data["id"])) if data.get("id") else None,
                    )
                    result["status"] = "SUCCESS"
                else:
                    result["status"] = "SKIPPED"
                    result["note"] = "No notification target resolved"
            elif action_type == "CREATE_AUDIT_EVENT":
                from app.models.audit import AuditEvent
                db.add(AuditEvent(
                    organization_id=workflow.organization_id,
                    actor_user_id=actor_user_id,
                    event_type=config.get("event_type", "WORKFLOW_CUSTOM_EVENT"),
                    entity_type=config.get("entity_type", "WORKFLOW"),
                    entity_id=execution.id,
                    metadata_=config.get("details", {}),
                ))
                db.flush()
                result["status"] = "SUCCESS"
            elif action_type == "TRIGGER_AUTOMATION":
                from app.services.automation_engine import handle_event
                payload = dict(data)
                payload.update({
                    "organization_id": str(workflow.organization_id),
                    "event_type": config.get("automation_event", "WORKFLOW_TRANSITION"),
                    "automation_id": config.get("automation_id"),
                })
                import asyncio as _asyncio
                try:
                    loop = _asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                            pool.submit(_asyncio.run, handle_event(db, payload)).result(timeout=30)
                    else:
                        loop.run_until_complete(handle_event(db, payload))
                except RuntimeError:
                    _asyncio.run(handle_event(db, payload))
                result["status"] = "SUCCESS"
            elif action_type == "REQUEST_APPROVAL":
                approval = WorkflowApproval(
                    workflow_transition_id=transition.id,
                    entity_type=data.get("entity_kind", "TASK"),
                    entity_id=UUID(str(data.get("id"))) if data.get("id") else execution.entity_id,
                    requested_by=actor_user_id,
                    status="PENDING",
                )
                db.add(approval)
                db.flush()
                result["status"] = "SUCCESS"
                result["approval_id"] = str(approval.id)
            else:
                result["status"] = "SKIPPED"
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
        results.append(result)
    return results


def apply_transition(db: Session, workflow: Workflow, execution: WorkflowExecution,
                     transition: WorkflowTransition, actor_user_id: Optional[UUID],
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Apply a transition to an execution, honoring conditions + approval gate."""
    context = context or {}
    data = get_entity_data(db, workflow.organization_id, execution.entity_type, execution.entity_id)
    data.update(context)
    data.setdefault("id", str(execution.entity_id))
    data.setdefault("entity_kind", execution.entity_type)

    # 1. Conditions (safe engine)
    passed, evaluations = evaluate_transition_conditions(transition, data)
    if not passed:
        db.add(WorkflowExecutionEvent(
            execution_id=execution.id, event_type="CONDITION_FAILED",
            from_state_id=execution.current_state_id, to_state_id=transition.to_state_id,
            actor_user_id=actor_user_id,
            metadata_={"transition": transition.name, "evaluations": evaluations},
        ))
        db.commit()
        return {"status": "BLOCKED", "reason": "Conditions not met", "evaluations": evaluations}

    # 2. Approval gate
    approval_cfg = transition.approval_config or {}
    needs_approval = transition.requires_approval or approval_cfg.get("required")
    pending = db.query(WorkflowApproval).filter(
        WorkflowApproval.workflow_transition_id == transition.id,
        WorkflowApproval.entity_id == execution.entity_id,
        WorkflowApproval.status == "PENDING",
    ).count()
    if needs_approval and pending == 0:
        from app.models.organization import OrganizationRole
        approver_type = approval_cfg.get("approver_type", "ROLE")
        approver_user_id = None
        if approver_type == "USER" and approval_cfg.get("approver_user_id"):
            approver_user_id = UUID(str(approval_cfg["approver_user_id"]))
        elif approver_type == "ROLE" and approval_cfg.get("organization_role"):
            from app.models.organization import OrganizationMember
            role = OrganizationRole(approval_cfg["organization_role"]) if approval_cfg["organization_role"] in OrganizationRole.__members__ else OrganizationRole.ADMIN
            member = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == workflow.organization_id,
                OrganizationMember.role == role,
            ).first()
            if member:
                approver_user_id = member.user_id
        elif approver_type == "TEAM" and approval_cfg.get("team_id"):
            from app.models.organization import TeamMember
            tm = db.query(TeamMember).filter(TeamMember.team_id == UUID(str(approval_cfg["team_id"]))).first()
            if tm:
                approver_user_id = tm.user_id

        db.add(WorkflowApproval(
            workflow_transition_id=transition.id,
            entity_type=execution.entity_type,
            entity_id=execution.entity_id,
            requested_by=actor_user_id,
            approver_user_id=approver_user_id,
            status="PENDING",
            comment=f"Requested by transition \"{transition.name}\"",
        ))
        db.add(WorkflowExecutionEvent(
            execution_id=execution.id, event_type="APPROVAL_REQUESTED",
            from_state_id=execution.current_state_id, to_state_id=transition.to_state_id,
            actor_user_id=actor_user_id,
            metadata_={"transition": transition.name, "approver_type": approver_type},
        ))
        db.commit()
        record_event(
            db=db, organization_id=workflow.organization_id, event_type="workflow.approval_requested",
            entity_type="WORKFLOW", actor_user_id=actor_user_id, entity_id=execution.id,
            metadata={"transition_id": str(transition.id), "transition": transition.name},
        )
        return {"status": "PENDING_APPROVAL", "transition": transition.name}

    # 3. Actions
    action_results = execute_workflow_actions(db, workflow, execution, transition, actor_user_id, data)
    failed_actions = [r for r in action_results if r.get("status") == "FAILED"]

    # 4. Move state
    from_state_id = execution.current_state_id
    execution.current_state_id = transition.to_state_id
    to_state = db.query(WorkflowState).filter(WorkflowState.id == transition.to_state_id).first()
    terminal = bool(to_state and to_state.is_terminal)
    db.add(WorkflowExecutionEvent(
        execution_id=execution.id, event_type="TRANSITION",
        from_state_id=from_state_id, to_state_id=transition.to_state_id,
        actor_user_id=actor_user_id,
        metadata_={"transition": transition.name, "actions": action_results},
    ))

    if failed_actions:
        execution.status = "FAILED"
        execution.error_message = "; ".join(r.get("error", "action failed") for r in failed_actions)
        execution.completed_at = datetime.now(timezone.utc)
        db.commit()
        record_event(db=db, organization_id=workflow.organization_id, event_type="workflow.execution_failed",
                     entity_type="WORKFLOW", actor_user_id=actor_user_id, entity_id=execution.id,
                     metadata={"workflow_id": str(workflow.id), "error": execution.error_message})
        broadcast_workflow_event(workflow.organization_id, "workflow.execution.failed", {
            "workflow_id": str(workflow.id), "execution_id": str(execution.id),
        })
        return {"status": "FAILED", "actions": action_results, "error": execution.error_message}

    if terminal:
        execution.status = "COMPLETED"
        execution.completed_at = datetime.now(timezone.utc)
        db.add(WorkflowExecutionEvent(
            execution_id=execution.id, event_type="COMPLETED",
            from_state_id=from_state_id, to_state_id=transition.to_state_id,
            actor_user_id=actor_user_id, metadata_={},
        ))
        db.commit()
        record_event(db=db, organization_id=workflow.organization_id, event_type="workflow.execution_completed",
                     entity_type="WORKFLOW", actor_user_id=actor_user_id, entity_id=execution.id,
                     metadata={"workflow_id": str(workflow.id)})
        broadcast_workflow_event(workflow.organization_id, "workflow.execution.completed", {
            "workflow_id": str(workflow.id), "execution_id": str(execution.id),
        })
    else:
        db.commit()
    db.refresh(execution)
    return {"status": "APPLIED", "transition": transition.name, "actions": action_results,
            "current_state": to_state.name if to_state else None,
            "execution_status": execution.status}


# ---------------------------------------------------------------------------
# Simulation (dry-run — never persists workflow state changes)
# ---------------------------------------------------------------------------

def simulate_workflow(db: Session, workflow: Workflow, entity_type: str = "TASK",
                      entity_id: Optional[UUID] = None, sample_data: Optional[Dict[str, Any]] = None,
                      start_state_id: Optional[UUID] = None,
                      target_state_id: Optional[UUID] = None) -> Dict[str, Any]:
    """Walk the workflow step by step in a dry-run context.

    Never writes WorkflowExecution rows, never mutates entities, and never
    executes actions — the result is a preview only.
    """
    states = {s.id: s for s in workflow.states}
    transitions = list(workflow.transitions or [])

    data: Dict[str, Any] = dict(sample_data or {})
    if entity_id:
        live = get_entity_data(db, workflow.organization_id, entity_type, entity_id)
        if live:
            data = {**data, **live}
    data.setdefault("entity_kind", entity_type)

    start = states.get(start_state_id) if start_state_id else next((s for s in states.values() if s.is_initial), None)
    if not start:
        return {
            "dry_run": True, "entity_type": entity_type, "status": "FAIL",
            "start_state": None, "end_state": None, "steps": [],
            "summary": "No starting state available (workflow has no initial state)",
            "workflow_version_id": None,
        }

    steps: List[Dict[str, Any]] = []
    current = start
    visited_states = 0
    status = "PASS"
    summary = None

    while not current.is_terminal and visited_states < MAX_SIMULATION_STEPS:
        visited_states += 1
        outgoing = [t for t in transitions if t.from_state_id == current.id]
        chosen = None
        evaluations: List[Dict[str, Any]] = []
        conditions_result = None

        if not outgoing:
            status = "FAIL"
            steps.append({
                "step_number": len(steps) + 1,
                "from_state": current.name,
                "to_state": None,
                "transition_name": None,
                "condition_evaluations": [],
                "conditions_result": None,
                "actions": [],
                "result": "FAIL",
                "detail": f"Dead end: state \"{current.name}\" has no outgoing transitions",
            })
            summary = f"Simulation stopped: no outgoing transitions from \"{current.name}\""
            break

        for t in sorted(outgoing, key=lambda x: x.position or 0):
            ok, evals = evaluate_transition_conditions(t, data)
            if target_state_id and t.to_state_id != target_state_id:
                evals = [{"field": "*", "operator": "TARGET_FILTER", "value": None, "result": False}] + evals
                continue
            chosen = t
            conditions_result = ok
            evaluations = evals
            break

        if chosen is None:
            status = "FAIL"
            steps.append({
                "step_number": len(steps) + 1,
                "from_state": current.name,
                "to_state": None,
                "transition_name": None,
                "condition_evaluations": evaluations,
                "conditions_result": False,
                "actions": [],
                "result": "FAIL",
                "detail": "No transition conditions passed from this state",
            })
            summary = "Simulation stopped: no transition conditions passed"
            break

        if not conditions_result:
            status = "FAIL"
            steps.append({
                "step_number": len(steps) + 1,
                "from_state": current.name,
                "to_state": states[chosen.to_state_id].name if chosen.to_state_id in states else None,
                "transition_name": chosen.name,
                "condition_evaluations": evaluations,
                "conditions_result": False,
                "actions": [],
                "result": "FAIL",
                "detail": "Transition conditions not satisfied by the sample data",
            })
            summary = f"Conditions for \"{chosen.name}\" evaluated to FAIL"
            break

        next_state = states.get(chosen.to_state_id)
        approval_cfg = chosen.approval_config or {}
        blocked = bool(chosen.requires_approval or approval_cfg.get("required"))

        action_results = execute_workflow_actions(
            db, workflow, None, chosen, None, data, dry_run=True
        ) if not blocked else []

        step_result = "BLOCKED" if blocked else "PASS"
        if blocked and status == "PASS":
            status = "BLOCKED"
        steps.append({
            "step_number": len(steps) + 1,
            "from_state": current.name,
            "to_state": next_state.name if next_state else None,
            "transition_name": chosen.name,
            "condition_evaluations": evaluations,
            "conditions_result": True,
            "actions": action_results,
            "result": step_result,
            "detail": "Approval required — simulation stops at the approval gate" if blocked else None,
        })

        if blocked:
            summary = f"Simulation paused at approval gate before \"{next_state.name if next_state else '?'}\""
            break

        if next_state is None:
            status = "FAIL"
            summary = "Transition target state missing"
            break

        current = next_state

    if current.is_terminal and not summary:
        summary = f"Simulation completed at terminal state \"{current.name}\""
    elif not summary:
        summary = f"Simulation stopped after {MAX_SIMULATION_STEPS} steps (possible circular transitions)"

    return {
        "dry_run": True,
        "entity_type": entity_type,
        "start_state": start.name,
        "end_state": current.name,
        "steps": steps,
        "status": status,
        "summary": summary,
        "workflow_version_id": None,
    }


# ---------------------------------------------------------------------------
# Form configuration validation (advanced form builder)
# ---------------------------------------------------------------------------

def validate_form_config(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate a form field configuration. Returns a list of issues."""
    issues: List[Dict[str, Any]] = []
    seen_ids = set()
    for f in fields or []:
        label = f.get("label") or "(untitled)"
        if not f.get("label"):
            issues.append({"severity": "ERROR", "code": "FORM_FIELD_LABEL", "message": "A form field is missing a label"})
        if f.get("type") not in FORM_FIELD_TYPES:
            issues.append({"severity": "ERROR", "code": "FORM_FIELD_TYPE",
                           "message": f"Field \"{label}\" has unsupported type \"{f.get('type')}\""})
        fid = f.get("id")
        if fid:
            if fid in seen_ids:
                issues.append({"severity": "ERROR", "code": "FORM_FIELD_DUPLICATE",
                               "message": f"Duplicate field id \"{fid}\""})
            seen_ids.add(fid)
        if f.get("type") == "CUSTOM_FIELD" and not f.get("custom_field_id"):
            issues.append({"severity": "ERROR", "code": "FORM_FIELD_CUSTOM_FIELD",
                           "message": f"Field \"{label}\" must link to an existing CustomField"})
        vis = f.get("visibility") or {}
        if vis:
            if not vis.get("field"):
                issues.append({"severity": "ERROR", "code": "FORM_FIELD_VISIBILITY",
                               "message": f"Field \"{label}\" has a visibility rule without a source field"})
            elif vis.get("operator") not in SAFE_OPERATORS:
                issues.append({"severity": "ERROR", "code": "FORM_FIELD_VISIBILITY",
                               "message": f"Field \"{label}\" uses unsupported visibility operator \"{vis.get('operator')}\""})
            if vis.get("action") not in (None, "SHOW", "HIDE"):
                issues.append({"severity": "ERROR", "code": "FORM_FIELD_VISIBILITY",
                               "message": f"Field \"{label}\" visibility action must be SHOW or HIDE"})
        validation = f.get("validation") or {}
        if validation:
            for key in ("min", "max", "minLength", "maxLength"):
                if key in validation and not isinstance(validation[key], (int, float)):
                    issues.append({"severity": "ERROR", "code": "FORM_FIELD_VALIDATION",
                                   "message": f"Field \"{label}\" validation \"{key}\" must be numeric"})
            pattern = validation.get("pattern")
            if pattern:
                import re
                try:
                    re.compile(str(pattern))
                except re.error:
                    issues.append({"severity": "ERROR", "code": "FORM_FIELD_VALIDATION",
                                   "message": f"Field \"{label}\" has an invalid regex pattern"})
    return issues


def evaluate_form_visibility(fields: List[Dict[str, Any]], answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute which fields are visible given answers (safe operators only)."""
    visible: List[Dict[str, Any]] = []
    for f in fields or []:
        vis = f.get("visibility") or {}
        if vis and vis.get("field"):
            source = answers.get(vis["field"])
            rule = {"field": vis["field"], "operator": vis.get("operator", "EQUALS"), "value": vis.get("value")}
            passed = evaluate_condition(rule, {vis["field"]: source})
            action = vis.get("action", "SHOW")
            if action == "HIDE" and passed:
                continue
            if action == "SHOW" and not passed:
                continue
        visible.append(f)
    return visible
