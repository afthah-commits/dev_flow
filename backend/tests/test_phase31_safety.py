"""Phase 31 — automation engine safety + AI advisory-only guarantees.

Covers:
- Nested ALL/ANY/NOT condition evaluation (safe engine, no eval/exec)
- handle_event idempotency (re-delivered events never double-execute)
- Action execution with correct tenant scoping (Phase 31 fixes)
- Cross-org UPDATE_TASK rejected through project scoping
- AI endpoints generate previews only — zero rows written, zero automations
  or workflows created, no execution possible without explicit human action
- Static guarantee: no eval()/exec()/os.system in the backend source
"""
import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.automation import Automation, AutomationExecution
from app.models.collaboration import Comment
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.core.security import create_access_token
from app.services.automation_engine import (
    evaluate_condition, evaluate_condition_group, handle_event,
)


# ---------------------------------------------------------------------------
# Condition engine: nested logical groups, no dynamic execution
# ---------------------------------------------------------------------------

def test_nested_condition_groups():
    payload = {"task": {"status": "OVERDUE", "points": 8}, "actor": "bot"}

    nested_all_any = {
        "logical_operator": "ALL",
        "conditions": [
            {"field": "task.status", "operator": "EQUALS", "value": "OVERDUE"},
            {
                "logical_operator": "ANY",
                "conditions": [
                    {"field": "task.points", "operator": "GREATER_THAN", "value": 5},
                    {"field": "actor", "operator": "EQUALS", "value": "human"},
                ],
            },
        ],
    }
    assert evaluate_condition_group(nested_all_any, payload) is True

    # Flipping the nested ANY makes the whole ALL fail
    nested_all_any["conditions"][1]["conditions"][0]["value"] = 99
    assert evaluate_condition_group(nested_all_any, payload) is False


def test_not_operator_group():
    payload = {"flag": True}
    group = {
        "logical_operator": "NOT",
        "conditions": [{"field": "flag", "operator": "EQUALS", "value": True}],
    }
    assert evaluate_condition_group(group, payload) is False

    group["conditions"][0]["value"] = False
    assert evaluate_condition_group(group, payload) is True


def test_unsafe_operator_is_rejected_not_executed():
    # A hostile "operator" never executes anything — unknown operators -> False
    payload = {"x": "__import__('os').system('id')"}
    assert evaluate_condition(
        {"field": "x", "operator": "__import__", "value": "y"}, payload
    ) is False
    # Empty group is permissive by design (matches Phase 29 behavior)
    assert evaluate_condition_group({}, payload) is True


# ---------------------------------------------------------------------------
# handle_event: gating + idempotency
# ---------------------------------------------------------------------------

def _seed_org(db: Session, suffix: str):
    user = User(id=uuid.uuid4(), name=f"Safety {suffix}",
                email=f"safety_{suffix}_{uuid.uuid4().hex[:6]}@test.com", password_hash="pwd")
    org = Organization(id=uuid.uuid4(), name=f"Safety Org {suffix}",
                       slug=f"safety-{suffix}-{uuid.uuid4().hex[:6]}", created_by=user.id)
    db.add(user)
    db.commit()
    db.add(org)
    db.commit()
    db.add(OrganizationMember(organization_id=org.id, user_id=user.id,
                              role=OrganizationRole.OWNER))
    db.commit()
    return user, org


def _project(db: Session, org, user, suffix: str) -> Project:
    project = Project(id=uuid.uuid4(), name=f"Proj {suffix}",
                      slug=f"proj-{suffix}-{uuid.uuid4().hex[:6]}",
                      organization_id=org.id, owner_id=user.id)
    db.add(project)
    db.commit()
    return project


def test_handle_event_gated_by_conditions_and_idempotent(db: Session):
    user, org = _seed_org(db, "evt")
    project = _project(db, org, user, "evt")
    task = Task(id=uuid.uuid4(), project_id=project.id, creator_id=user.id,
                title="T", status=TaskStatus.TODO, priority="MEDIUM")
    db.add(task)
    db.commit()

    comment_automation = Automation(
        organization_id=str(org.id),
        created_by=str(user.id),
        name="Notify on overdue",
        trigger_type="TASK_STATUS_CHANGED",
        enabled=True,
        conditions={
            "logical_operator": "ALL",
            "conditions": [
                {"field": "task.status", "operator": "EQUALS", "value": "OVERDUE"},
            ],
        },
        actions=[{"type": "CREATE_COMMENT", "content": "auto note",
                  "entity_id": str(task.id)}],
    )
    db.add(comment_automation)
    db.commit()
    automation_id = comment_automation.id

    base_payload = {
        "organization_id": str(org.id),
        "event_type": "TASK_STATUS_CHANGED",
        "entity_id": str(task.id),
        "task": {"status": "OVERDUE"},
        "timestamp": "2026-10-05T00:00:00Z",
    }

    import asyncio

    # Non-matching payload: no execution, no comment
    mismatch = dict(base_payload, task={"status": "TODO"})
    asyncio.run(handle_event(db, mismatch))
    assert db.query(AutomationExecution).filter(
        AutomationExecution.automation_id == automation_id).count() == 0
    assert db.query(Comment).filter(Comment.entity_id == task.id).count() == 0

    # Matching payload: execution + comment created
    asyncio.run(handle_event(db, base_payload))
    executions = db.query(AutomationExecution).filter(
        AutomationExecution.automation_id == automation_id).all()
    assert len(executions) == 1
    if executions[0].status != "SUCCESS":
        print("STATUS IS:", executions[0].status)
        print("ERROR MESSAGE:", executions[0].error_message)
        action_execs = db.query(AutomationActionExecution).filter(AutomationActionExecution.execution_id == executions[0].id).all()
        for ae in action_execs:
            print("ACTION OUTPUT:", ae.output_data)
    assert executions[0].status == "SUCCESS"
    assert db.query(Comment).filter(Comment.entity_id == task.id).count() == 1

    # Same event redelivered (same idempotency key): NO second execution
    asyncio.run(handle_event(db, dict(base_payload)))
    assert db.query(AutomationExecution).filter(
        AutomationExecution.automation_id == automation_id).count() == 1
    assert db.query(Comment).filter(Comment.entity_id == task.id).count() == 1


# ---------------------------------------------------------------------------
# Action execution: tenant scoping (Phase 31 fixes)
# ---------------------------------------------------------------------------

def test_create_task_action_needs_actor_and_project(db: Session):
    """CREATE_TASK without actor/project fails cleanly — no TypeError crash."""
    user, org = _seed_org(db, "ct")
    automation = Automation(
        organization_id=str(org.id), created_by=str(user.id),
        name="Create task", trigger_type="TASK_CREATED", enabled=True,
        conditions={},
        actions=[{"type": "CREATE_TASK", "title": "From automation"}],
    )
    db.add(automation)
    db.commit()

    import asyncio
    payload = {"organization_id": str(org.id), "event_type": "TASK_CREATED",
               "entity_id": str(uuid.uuid4()), "timestamp": "t1"}
    asyncio.run(handle_event(db, payload))

    execution = db.query(AutomationExecution).filter(
        AutomationExecution.automation_id == automation.id).one()
    assert execution.status == "FAILED"  # clean failure, engine survived


def test_create_task_action_succeeds_with_actor(db: Session):
    user, org = _seed_org(db, "ct2")
    project = _project(db, org, user, "ct2")
    automation = Automation(
        organization_id=str(org.id), created_by=str(user.id),
        name="Create task ok", trigger_type="TASK_CREATED", enabled=True,
        conditions={},
        actions=[{"type": "CREATE_TASK", "title": "From automation"}],
    )
    db.add(automation)
    db.commit()

    import asyncio
    payload = {"organization_id": str(org.id), "event_type": "TASK_CREATED",
               "entity_id": str(uuid.uuid4()), "timestamp": "t2",
               "project_id": str(project.id), "actor_user_id": str(user.id)}
    asyncio.run(handle_event(db, payload))

    execution = db.query(AutomationExecution).filter(
        AutomationExecution.automation_id == automation.id).one()
    assert execution.status == "SUCCESS"
    created = db.query(Task).filter(Task.title == "From automation").all()
    assert len(created) == 1
    assert created[0].project_id == project.id
    assert created[0].creator_id == user.id


def test_update_task_action_is_tenant_scoped(db: Session):
    """ORG-B automation cannot touch ORG-A's task through UPDATE_TASK."""
    user_a, org_a = _seed_org(db, "iso-a")
    project_a = _project(db, org_a, user_a, "iso-a")
    task_a = Task(id=uuid.uuid4(), project_id=project_a.id, creator_id=user_a.id,
                  title="Org A task", status=TaskStatus.TODO, priority="MEDIUM")
    db.add(task_a)
    db.commit()

    user_b, org_b = _seed_org(db, "iso-b")
    automation_b = Automation(
        organization_id=str(org_b.id), created_by=str(user_b.id),
        name="Evil updater", trigger_type="TASK_STATUS_CHANGED", enabled=True,
        conditions={},
        actions=[{"type": "UPDATE_TASK", "task_id": str(task_a.id),
                  "status": "DONE"}],
    )
    db.add(automation_b)
    db.commit()

    import asyncio
    payload = {"organization_id": str(org_b.id), "event_type": "TASK_STATUS_CHANGED",
               "entity_id": str(task_a.id), "timestamp": "t3"}
    asyncio.run(handle_event(db, payload))

    execution = db.query(AutomationExecution).filter(
        AutomationExecution.automation_id == automation_b.id).one()
    action_execs = execution.action_executions if hasattr(execution, "action_executions") else []
    # The action must not have updated the foreign task
    db.refresh(task_a)
    assert task_a.status == TaskStatus.TODO, "cross-org UPDATE_TASK must not mutate the task"


# ---------------------------------------------------------------------------
# AI advisory-only guarantees
# ---------------------------------------------------------------------------

def _register(client: TestClient, email: str) -> dict:
    client.post("/api/v1/auth/register",
                json={"name": email.split("@")[0], "email": email, "password": "password123"})
    token = client.post("/api/v1/auth/login",
                        json={"email": email, "password": "password123"}).json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    org = client.post("/api/v1/organizations", json={"name": "AI Safety"}, headers=auth).json()
    return {**auth, "X-Organization-Id": org["id"]}


def test_ai_automation_generate_is_preview_only(client: TestClient, db: Session):
    headers = _register(client, "ai-safety@example.com")

    before = db.query(Automation).count()
    res = client.post("/api/v1/ai/automations/generate",
                      json={"prompt": "when a task goes overdue, notify the PM"},
                      headers=headers)
    assert res.status_code == 200
    suggestion = res.json()
    # Advisory response only — nothing persisted, nothing executed
    assert db.query(Automation).count() == before
    assert db.query(AutomationExecution).count() == 0
    assert "trigger_type" in suggestion and "actions" in suggestion


def test_ai_workflow_generate_is_preview_only(client: TestClient, db: Session):
    from app.models.workflow import Workflow
    headers = _register(client, "ai-safety-wf@example.com")

    before = db.query(Workflow).count()
    res = client.post("/api/v1/ai/workflows/generate",
                      json={"prompt": "block overdue tasks and require approval"},
                      headers=headers)
    assert res.status_code == 200
    body = res.json()
    # Preview contract: explicit preview flag, zero workflows created
    assert body.get("preview_only") is True
    assert db.query(Workflow).count() == before


def test_ai_endpoints_require_authentication(client: TestClient):
    assert client.post("/api/v1/ai/automations/generate",
                       json={"prompt": "x"}).status_code == 401
    assert client.post("/api/v1/ai/workflows/generate",
                       json={"prompt": "x"}).status_code == 401
    assert client.get("/api/v1/ai/usage").status_code == 401


def test_ai_cannot_publish_or_execute_workflows(client: TestClient, db: Session):
    """AI generation endpoints never expose publish/execute side effects."""
    headers = _register(client, "ai-safety-pub@example.com")

    # Generating a suggestion returns a preview and gives us no workflow id
    # to act on — and the publish endpoint still requires a real workflow +
    # workflows.publish permission (covered by Phase 30 RBAC matrix).
    res = client.post("/api/v1/ai/workflows/generate",
                      json={"prompt": "publish immediately"}, headers=headers)
    assert res.status_code == 200
    assert "id" not in res.json() or res.json().get("preview_only") is True


# ---------------------------------------------------------------------------
# Static guarantee: no dynamic execution in backend source
# ---------------------------------------------------------------------------

def test_backend_source_contains_no_dynamic_execution():
    backend_root = Path(__file__).resolve().parent.parent / "app"
    offenders = []
    import re
    pattern = re.compile(
        r"(?<![\w.])(eval|exec)\s*\(|os\.system\s*\(|subprocess\.[a-z]+\s*\(|shell=True"
    )
    for path in backend_root.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Ignore documentation phrasing like "(no eval())" / "never eval("
            checked = line.replace("no eval()", "").replace("no exec()", "")
            if pattern.search(checked):
                offenders.append(f"{path}:{lineno}: {stripped[:100]}")
    assert not offenders, "dynamic execution found:\n" + "\n".join(offenders)
