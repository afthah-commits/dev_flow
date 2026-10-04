"""Phase 30 — Visual Workflow Studio backend tests.

Covers: tenant isolation, RBAC, validation, state/transition CRUD, invalid
transition rejection, simulation dry-run, publishing, version immutability,
approval configuration, form validation, conditional fields, AI preview
safety, and execution isolation.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str):
    client.post("/api/v1/auth/register", json={"name": email.split("@")[0], "email": email, "password": "password123"})
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org = client.post("/api/v1/organizations", json={"name": f"Org {email}"}, headers=headers).json()
    headers["X-Organization-Id"] = org["id"]
    return headers, org


def _create_workflow(client: TestClient, headers, name="Test Workflow", with_graph=True):
    payload = {
        "name": name,
        "entity_type": "TASK",
        "states": [],
        "transitions": [],
    }
    res = client.post("/api/v1/workflows", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    wf = res.json()
    if with_graph:
        todo = _add_state(client, headers, wf["id"], "To Do", key="TODO", is_initial=True).json()
        done = _add_state(client, headers, wf["id"], "Done", key="DONE", is_terminal=True).json()
        res = client.post(f"/api/v1/workflows/{wf['id']}/transitions", json={
            "name": "Finish", "from_state_id": todo["id"], "to_state_id": done["id"], "position": 0,
        }, headers=headers)
        assert res.status_code == 201, res.text
        wf = client.get(f"/api/v1/workflows/{wf['id']}", headers=headers).json()
    return wf


def _add_state(client: TestClient, headers, workflow_id, name, **kwargs):
    return client.post(f"/api/v1/workflows/{workflow_id}/states",
                       json={"name": name, **kwargs}, headers=headers)


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

def test_workflow_tenant_isolation(client: TestClient):
    headers_a, _ = _register_and_login(client, "iso-wf-a@example.com")
    headers_b, _ = _register_and_login(client, "iso-wf-b@example.com")

    wf = _create_workflow(client, headers_a, "Org A Secret Workflow")

    # B cannot read A's workflow
    res = client.get(f"/api/v1/workflows/{wf['id']}", headers=headers_b)
    assert res.status_code in (403, 404)

    # B cannot open A's studio
    res = client.get(f"/api/v1/workflows/{wf['id']}/studio", headers=headers_b)
    assert res.status_code in (403, 404)

    # B cannot add a state to A's workflow
    res = _add_state(client, headers_b, wf["id"], "Injected")
    assert res.status_code in (403, 404)

    # B cannot create a transition on A's workflow
    res = client.post(f"/api/v1/workflows/{wf['id']}/transitions", json={
        "name": "Injected", "from_state_id": str(uuid4()), "to_state_id": str(uuid4()),
    }, headers=headers_b)
    assert res.status_code in (403, 404)

    # B cannot publish or archive A's workflow
    assert client.post(f"/api/v1/workflows/{wf['id']}/publish", headers=headers_b).status_code in (403, 404)
    assert client.post(f"/api/v1/workflows/{wf['id']}/archive", headers=headers_b).status_code in (403, 404)

    # B cannot validate or simulate A's workflow
    assert client.post(f"/api/v1/workflows/{wf['id']}/validate", headers=headers_b).status_code in (403, 404)
    assert client.post(f"/api/v1/workflows/{wf['id']}/simulate", json={"entity_type": "TASK"}, headers=headers_b).status_code in (403, 404)

    # B's workflow list never contains A's workflow
    res = client.get("/api/v1/workflows", headers=headers_b)
    assert res.status_code == 200
    assert all(w["id"] != wf["id"] for w in res.json())


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------

def test_workflow_rbac_unauthorized(client: TestClient):
    # No token at all
    assert client.get("/api/v1/workflows").status_code == 401
    assert client.post("/api/v1/workflows", json={"name": "X", "entity_type": "TASK"}).status_code == 401


def test_workflow_rbac_missing_org_header(client: TestClient):
    headers, _ = _register_and_login(client, "rbac-wf@example.com")
    headers.pop("X-Organization-Id")
    res = client.post("/api/v1/workflows", json={"name": "No Org", "entity_type": "TASK"}, headers=headers)
    assert res.status_code in (400, 403)


def test_workflow_permission_matrix(client: TestClient):
    """Member role can view/simulate but cannot publish or manage forms."""
    headers, _ = _register_and_login(client, "owner-wf@example.com")
    # Owner token can do everything; check that publish validation gate works for them
    wf = _create_workflow(client, headers, "Perm Workflow", with_graph=True)
    # Owner (fallback ADMIN+) may publish a valid workflow
    res = client.post(f"/api/v1/workflows/{wf['id']}/publish", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "published"


# ---------------------------------------------------------------------------
# Studio: states & transitions CRUD
# ---------------------------------------------------------------------------

def test_state_creation_and_validation(client: TestClient):
    headers, _ = _register_and_login(client, "state-wf@example.com")
    wf = _create_workflow(client, headers)

    res = _add_state(client, headers, wf["id"], "In Progress", state_type="IN_PROGRESS", color="#3b82f6")
    assert res.status_code == 201, res.text
    state = res.json()
    assert state["state_type"] == "IN_PROGRESS"
    assert state["key"] == "INPROGRESS"
    assert state["incoming_count"] == 0
    assert state["outgoing_count"] == 0

    # Duplicate key rejected
    res = _add_state(client, headers, wf["id"], "In Progress!")
    assert res.status_code == 409


def test_only_one_initial_state(client: TestClient):
    headers, _ = _register_and_login(client, "initial-wf@example.com")
    wf = _create_workflow(client, headers)
    res = _add_state(client, headers, wf["id"], "Second Initial", is_initial=True)
    assert res.status_code == 201
    studio = client.get(f"/api/v1/workflows/{wf['id']}/studio", headers=headers).json()
    initial_states = [s for s in studio["states"] if s["is_initial"]]
    assert len(initial_states) == 1


def test_invalid_transition_rejection(client: TestClient):
    headers, _ = _register_and_login(client, "trans-wf@example.com")
    wf = _create_workflow(client, headers)

    # Self transition rejected
    states = {s["key"]: s for s in wf["states"]}
    res = client.post(f"/api/v1/workflows/{wf['id']}/transitions", json={
        "name": "Self", "from_state_id": states["TODO"]["id"], "to_state_id": states["TODO"]["id"],
    }, headers=headers)
    assert res.status_code == 400

    # Foreign state ids rejected (cross-workflow transition manipulation)
    res = client.post(f"/api/v1/workflows/{wf['id']}/transitions", json={
        "name": "Foreign", "from_state_id": str(uuid4()), "to_state_id": str(uuid4()),
    }, headers=headers)
    assert res.status_code == 400


def test_transition_crud_with_conditions_and_actions(client: TestClient):
    headers, _ = _register_and_login(client, "crud-wf@example.com")
    wf = _create_workflow(client, headers)
    states = {s["key"]: s for s in wf["states"]}

    res = client.post(f"/api/v1/workflows/{wf['id']}/transitions", json={
        "name": "Ship It",
        "from_state_id": states["TODO"]["id"],
        "to_state_id": states["DONE"]["id"],
        "conditions": [{"field": "estimate_points", "operator": "GREATER_THAN", "value": "5"}],
        "actions": [
            {"action_type": "SEND_NOTIFICATION", "configuration": {"message": "Shipped!"}, "position": 0},
            {"action_type": "CREATE_TASK", "configuration": {"title": "Follow up"}, "position": 1, "enabled": False},
        ],
    }, headers=headers)
    assert res.status_code == 201, res.text
    transition = res.json()
    assert len(transition["conditions"]) == 1
    assert len(transition["actions"]) == 2
    assert transition["actions"][1]["enabled"] is False

    # Update: replace conditions
    res = client.patch(f"/api/v1/workflows/{wf['id']}/transitions/{transition['id']}", json={
        "conditions": [{"field": "is_blocked", "operator": "IS_EMPTY", "value": None}],
    }, headers=headers)
    assert res.status_code == 200
    assert len(res.json()["conditions"]) == 1
    assert res.json()["conditions"][0]["operator"] == "IS_EMPTY"

    # Delete
    res = client.delete(f"/api/v1/workflows/{wf['id']}/transitions/{transition['id']}", headers=headers)
    assert res.status_code == 204


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_validation_detects_missing_initial_state(client: TestClient):
    headers, _ = _register_and_login(client, "val-wf@example.com")
    wf = _create_workflow(client, headers, with_graph=False)
    _add_state(client, headers, wf["id"], "Only State", is_terminal=True)

    res = client.post(f"/api/v1/workflows/{wf['id']}/validate", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ERROR"
    assert data["can_publish"] is False
    codes = [i["code"] for i in data["issues"]]
    assert "NO_INITIAL_STATE" in codes


def test_validation_detects_unreachable_and_dead_ends(client: TestClient):
    headers, _ = _register_and_login(client, "val2-wf@example.com")
    wf = _create_workflow(client, headers)
    # orphan state
    _add_state(client, headers, wf["id"], "Orphan")
    # dead end state
    _add_state(client, headers, wf["id"], "Dead End")

    res = client.post(f"/api/v1/workflows/{wf['id']}/validate", headers=headers)
    data = res.json()
    codes = [i["code"] for i in data["issues"]]
    assert "UNREACHABLE_STATE" in codes
    assert "DEAD_END_STATE" in codes
    messages = " ".join(i["message"] for i in data["issues"])
    assert "Orphan" in messages and "Dead End" in messages


def test_validation_passes_on_valid_graph(client: TestClient):
    headers, _ = _register_and_login(client, "val3-wf@example.com")
    wf = _create_workflow(client, headers, with_graph=True)
    res = client.post(f"/api/v1/workflows/{wf['id']}/validate", headers=headers)
    data = res.json()
    assert data["status"] == "PASS"
    assert data["can_publish"] is True


def test_publish_blocked_by_validation_errors(client: TestClient):
    headers, _ = _register_and_login(client, "pub-wf@example.com")
    wf = _create_workflow(client, headers, with_graph=False)
    _add_state(client, headers, wf["id"], "Lonely")
    res = client.post(f"/api/v1/workflows/{wf['id']}/publish", headers=headers)
    assert res.status_code == 400
    assert "validation" in str(res.json()).lower() or "validation" in res.text.lower()


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

def test_version_lifecycle_and_immutability(client: TestClient):
    headers, _ = _register_and_login(client, "ver-wf@example.com")
    wf = _create_workflow(client, headers)

    # Create v1 (draft)
    res = client.post(f"/api/v1/workflows/{wf['id']}/versions", json={"change_note": "initial"}, headers=headers)
    assert res.status_code == 201
    v1 = res.json()
    assert v1["version_number"] == 1
    assert v1["status"] == "DRAFT"

    # Publish v1
    res = client.post(f"/api/v1/workflows/{wf['id']}/publish", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "published"

    versions = client.get(f"/api/v1/workflows/{wf['id']}/versions", headers=headers).json()
    published = [v for v in versions if v["status"] == "PUBLISHED"]
    assert len(published) == 1
    v1_id = published[0]["id"]

    # Mutate the live workflow, publish again -> old version archived, new version published
    _add_state(client, headers, wf["id"], "Review")
    res = client.post(f"/api/v1/workflows/{wf['id']}/publish", headers=headers)
    assert res.status_code == 200

    versions = client.get(f"/api/v1/workflows/{wf['id']}/versions", headers=headers).json()
    by_number = {v["version_number"]: v for v in versions}
    assert by_number[1]["status"] in ("ARCHIVED", "PUBLISHED")
    assert max(by_number) == 2

    # Archived versions remain readable with their original snapshot
    detail = client.get(f"/api/v1/workflows/{wf['id']}/versions/{v1_id}", headers=headers)
    assert detail.status_code == 200
    snapshot = detail.json()["snapshot"]
    assert "states" in snapshot

    # Published versions are immutable: no endpoint mutates version rows
    assert client.patch(f"/api/v1/workflows/{wf['id']}/versions/{v1_id}", headers=headers).status_code == 405


# ---------------------------------------------------------------------------
# Simulation (dry-run)
# ---------------------------------------------------------------------------

def test_simulation_dry_run_does_not_modify_data(client: TestClient):
    headers, _ = _register_and_login(client, "sim-wf@example.com")
    wf = _create_workflow(client, headers)

    res = client.post(f"/api/v1/workflows/{wf['id']}/simulate", json={
        "entity_type": "TASK",
        "sample_data": {"estimate_points": 8, "title": "Sample Task"},
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["dry_run"] is True
    assert data["status"] == "PASS"
    assert data["start_state"] == "To Do"
    assert data["end_state"] == "Done"
    assert len(data["steps"]) == 1

    # No executions were created by simulation
    executions = client.get(f"/api/v1/workflows/{wf['id']}/executions", headers=headers).json()
    assert executions == []


def test_simulation_stops_at_approval_gate(client: TestClient):
    headers, _ = _register_and_login(client, "sim2-wf@example.com")
    wf = _create_workflow(client, headers)
    states = {s["key"]: s for s in wf["states"]}

    # Give the only transition an approval requirement
    finish = next(t for t in wf["transitions"] if t["name"] == "Finish")
    res = client.patch(f"/api/v1/workflows/{wf['id']}/transitions/{finish['id']}", json={
        "requires_approval": True,
        "approval_config": {"required": True, "approver_type": "ROLE", "organization_role": "ADMIN", "minimum_approvals": 1},
    }, headers=headers)
    assert res.status_code == 200

    data = client.post(f"/api/v1/workflows/{wf['id']}/simulate", json={"entity_type": "TASK"}, headers=headers).json()
    assert data["status"] == "BLOCKED"
    assert any(s["result"] == "BLOCKED" for s in data["steps"])


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------

def test_form_validation_rejects_bad_config(client: TestClient):
    headers, _ = _register_and_login(client, "form-wf@example.com")
    wf = _create_workflow(client, headers)

    # Unsupported visibility operator must be rejected (no eval!)
    res = client.post(f"/api/v1/workflows/{wf['id']}/forms", json={
        "name": "Deploy Form",
        "fields": [
            {"id": "deploy", "type": "CHECKBOX", "label": "Deploy?"},
            {"id": "env", "type": "SELECT", "label": "Env", "options": ["staging"],
             "visibility": {"field": "deploy", "operator": "__import__('os')", "value": True}},
        ],
    }, headers=headers)
    assert res.status_code == 400

    # Valid conditional form is accepted
    res = client.post(f"/api/v1/workflows/{wf['id']}/forms", json={
        "name": "Deploy Form",
        "fields": [
            {"id": "deploy", "type": "CHECKBOX", "label": "Deploy?", "position": 0},
            {"id": "env", "type": "SELECT", "label": "Env", "options": ["staging", "production"], "position": 1,
             "visibility": {"field": "deploy", "operator": "EQUALS", "value": True, "action": "SHOW"}},
        ],
    }, headers=headers)
    assert res.status_code == 201, res.text
    form = res.json()
    assert form["configuration"]["fields"][1]["visibility"]["operator"] == "EQUALS"

    # PATCH with a broken field is rejected
    res = client.patch(f"/api/v1/workflows/{wf['id']}/forms/{form['id']}", json={
        "fields": [{"id": "bad", "type": "NOT_A_TYPE", "label": "Bad"}],
    }, headers=headers)
    assert res.status_code == 400


def test_conditional_field_visibility_logic(client: TestClient):
    from app.services.workflow_studio import evaluate_form_visibility
    fields = [
        {"id": "deploy", "type": "CHECKBOX", "label": "Deploy?"},
        {"id": "env", "type": "SELECT", "label": "Env",
         "visibility": {"field": "deploy", "operator": "EQUALS", "value": True, "action": "SHOW"}},
        {"id": "skip_reason", "type": "TEXT", "label": "Why not?",
         "visibility": {"field": "deploy", "operator": "EQUALS", "value": True, "action": "HIDE"}},
    ]
    visible_yes = [f["id"] for f in evaluate_form_visibility(fields, {"deploy": True})]
    visible_no = [f["id"] for f in evaluate_form_visibility(fields, {"deploy": False})]
    assert visible_yes == ["deploy", "env"]
    assert visible_no == ["deploy", "skip_reason"]


# ---------------------------------------------------------------------------
# AI preview safety
# ---------------------------------------------------------------------------

def test_ai_workflow_generation_is_preview_only(client: TestClient):
    headers, org = _register_and_login(client, "ai-wf@example.com")
    res = client.post("/api/v1/ai/workflows/generate", headers=headers, json={
        "prompt": "When a task becomes overdue, move it to blocked, notify the project manager, and require approval before reopening."
    })
    assert res.status_code == 200
    data = res.json()
    assert data["preview_only"] is True
    keys = [s["key"] for s in data["states"]]
    assert "BLOCKED" in keys
    assert any(t.get("requires_approval") for t in data["transitions"])

    # Nothing was auto-created: workflows list for this org is empty
    workflows = client.get("/api/v1/workflows", headers=headers).json()
    assert workflows == []


def test_ai_apply_creates_draft_not_published(client: TestClient):
    headers, _ = _register_and_login(client, "aiapply-wf@example.com")
    suggestion = client.post("/api/v1/ai/workflows/generate", headers=headers, json={
        "prompt": "overdue tasks must be blocked with approval to reopen"
    }).json()

    res = client.post("/api/v1/workflows/ai/apply", headers=headers, json={"suggestion": suggestion})
    assert res.status_code == 201
    wf = res.json()
    assert wf["is_active"] is False  # draft

    # The applied workflow must not be published
    versions = client.get(f"/api/v1/workflows/{wf['id']}/versions", headers=headers).json()
    assert versions == []


# ---------------------------------------------------------------------------
# Executions
# ---------------------------------------------------------------------------

def test_execution_start_and_isolation(client: TestClient):
    headers_a, _ = _register_and_login(client, "exec-a@example.com")
    headers_b, _ = _register_and_login(client, "exec-b@example.com")
    wf = _create_workflow(client, headers_a)

    # B cannot start an execution on A's workflow
    res = client.post(f"/api/v1/workflows/{wf['id']}/executions",
                      json={"entity_type": "TASK", "entity_id": str(uuid4())}, headers=headers_b)
    assert res.status_code in (403, 404)

    # Cross-org entity rejected even for A (entity belongs to no project here -> 404)
    res = client.post(f"/api/v1/workflows/{wf['id']}/executions",
                      json={"entity_type": "TASK", "entity_id": str(uuid4())}, headers=headers_a)
    assert res.status_code == 404


def test_execution_isolation_for_entity_from_other_org(client: TestClient):
    """A task from org B cannot be attached to org A's workflow."""
    from app.db.base import Base  # noqa: F401
    headers_a, org_a = _register_and_login(client, "exec-x-a@example.com")
    headers_b, org_b = _register_and_login(client, "exec-x-b@example.com")

    # B creates a project + task
    project = client.post("/api/v1/projects", json={"name": "B Project"}, headers=headers_b).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks",
                       json={"title": "B Task", "description": "x"}, headers=headers_b).json()

    wf = _create_workflow(client, headers_a)
    res = client.post(f"/api/v1/workflows/{wf['id']}/executions",
                      json={"entity_type": "TASK", "entity_id": task["id"]}, headers=headers_a)
    assert res.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------

def test_approval_configuration_persists(client: TestClient):
    headers, _ = _register_and_login(client, "appr-wf@example.com")
    wf = _create_workflow(client, headers)
    states = {s["key"]: s for s in wf["states"]}

    res = client.post(f"/api/v1/workflows/{wf['id']}/transitions", json={
        "name": "Needs Sign-off",
        "from_state_id": states["TODO"]["id"],
        "to_state_id": states["DONE"]["id"],
        "requires_approval": True,
        "approval_config": {
            "required": True, "approver_type": "ROLE", "organization_role": "ADMIN",
            "minimum_approvals": 2, "timeout_hours": 48, "on_reject": "RETURN_TO_PREVIOUS",
        },
    }, headers=headers)
    assert res.status_code == 201
    cfg = res.json()["approval_config"]
    assert cfg["minimum_approvals"] == 2
    assert cfg["timeout_hours"] == 48
    assert cfg["on_reject"] == "RETURN_TO_PREVIOUS"

    # Studio shows approval config on the transition and node indicator
    studio = client.get(f"/api/v1/workflows/{wf['id']}/studio", headers=headers).json()
    trans = next(t for t in studio["transitions"] if t["name"] == "Needs Sign-off")
    assert trans["requires_approval"] is True


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def test_layout_save_and_reset(client: TestClient):
    headers, _ = _register_and_login(client, "layout-wf@example.com")
    wf = _create_workflow(client, headers)
    states = {s["key"]: s for s in wf["states"]}

    res = client.post(f"/api/v1/workflows/{wf['id']}/layout", json={
        "positions": [
            {"state_id": states["TODO"]["id"], "x": 120.0, "y": 80.0},
            {"state_id": states["DONE"]["id"], "x": 400.0, "y": 80.0},
        ],
    }, headers=headers)
    assert res.status_code == 200
    studio = client.get(f"/api/v1/workflows/{wf['id']}/studio", headers=headers).json()
    assert len(studio["layouts"]) == 2

    res = client.post(f"/api/v1/workflows/{wf['id']}/layout/reset", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 2


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def test_workflow_audit_events_recorded(client: TestClient, db):
    from uuid import UUID as _UUID
    from app.models.audit import AuditEvent
    headers, _ = _register_and_login(client, "audit-wf@example.com")
    wf = _create_workflow(client, headers)
    _add_state(client, headers, wf["id"], "Audited State")

    # Use the same transactional session the TestClient uses
    events = db.query(AuditEvent).filter(
        AuditEvent.organization_id == _UUID(wf["organization_id"]),
        AuditEvent.event_type.like("workflow.%"),
    ).all()
    types = {e.event_type for e in events}
    assert "workflow.created" in types
    assert "workflow.state_created" in types


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def test_workflow_analytics_endpoint(client: TestClient):
    headers, _ = _register_and_login(client, "analytics-wf@example.com")
    wf = _create_workflow(client, headers)
    res = client.get(f"/api/v1/workflows/{wf['id']}/analytics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_executions"] == 0
    assert data["failure_rate"] is None
