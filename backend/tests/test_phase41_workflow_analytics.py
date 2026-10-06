"""Phase 41 — Workflow analytics completion.

Covers:
- real average_execution_time (completed executions only, missing timestamps
  excluded, zero-safe)
- real blocked_executions (ACTIVE executions with a PENDING approval gate;
  FAILED executions are NOT blocked)
- organization isolation and response contract compatibility
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.workflow import (
    Workflow, WorkflowExecution, WorkflowApproval, WorkflowState, WorkflowTransition,
)
from app.schemas.analytics import WorkflowAnalyticsResponse


def _register(client, email):
    client.post("/api/v1/auth/register", json={"name": "P41", "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _user_by_email(db, email):
    return db.query(User).filter(User.email == email).first()


def _make_org(db, owner_id):
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=f"p41-{uuid4().hex[:8]}", created_by=owner_id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=owner_id,
                              role=OrganizationRole.OWNER))
    db.commit()
    return org


def _workflow(db, org, name="WF"):
    wf = Workflow(id=uuid4(), organization_id=org.id, name=name)
    db.add(wf)
    db.commit()
    return wf


def _execution(db, wf, status="ACTIVE", started=False, completed=None, entity_type="TASK"):
    """started=False means 'use the column default (now)'. Pass None to get a
    NULL start at the ORM level only — the schema forbids it (nullable=False),
    which is itself asserted by the missing-start test below."""
    ex = WorkflowExecution(
        id=uuid4(), workflow_id=wf.id, entity_type=entity_type, entity_id=uuid4(),
        status=status, started_at=started or None, completed_at=completed,
    )
    db.add(ex)
    db.commit()
    if started is None:
        db.expire(ex)
        ex.started_at = None
    return ex


def _pending_approval(db, wf, ex, status="PENDING"):
    """Approval rows require a real transition (NOT NULL FK)."""
    from_state = WorkflowState(id=uuid4(), workflow_id=wf.id, name="From", key=f"from-{uuid4().hex[:6]}", position=0)
    to_state = WorkflowState(id=uuid4(), workflow_id=wf.id, name="To", key=f"to-{uuid4().hex[:6]}", position=1)
    db.add_all([from_state, to_state])
    db.flush()
    transition = WorkflowTransition(
        id=uuid4(), workflow_id=wf.id, name="Gate",
        from_state_id=from_state.id, to_state_id=to_state.id, position=0,
    )
    db.add(transition)
    db.flush()
    approval = WorkflowApproval(
        id=uuid4(), workflow_transition_id=transition.id,
        entity_type=ex.entity_type, entity_id=ex.entity_id, status=status,
    )
    db.add(approval)
    db.commit()
    return approval


def _analytics(client, headers, org):
    return client.get("/api/v1/analytics/workflow", headers={
        **headers, "X-Organization-Id": str(org.id)})


# ---------------------------------------------------------------------------
# average_execution_time
# ---------------------------------------------------------------------------

def test_average_execution_time_zero_with_no_executions(client, db):
    headers = _register(client, "p41-empty@example.com")
    org = _make_org(db, _user_by_email(db, "p41-empty@example.com").id)
    _workflow(db, org)
    res = _analytics(client, headers, org)
    assert res.status_code == 200
    assert res.json()["average_execution_time"] == 0.0


def test_average_execution_time_single_completed_execution(client, db):
    headers = _register(client, "p41-one@example.com")
    org = _make_org(db, _user_by_email(db, "p41-one@example.com").id)
    wf = _workflow(db, org)
    start = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    _execution(db, wf, status="COMPLETED", started=start,
               completed=start + timedelta(seconds=120))
    res = _analytics(client, headers, org)
    assert res.json()["average_execution_time"] == pytest.approx(120.0)


def test_average_execution_time_multiple_completed(client, db):
    headers = _register(client, "p41-multi@example.com")
    org = _make_org(db, _user_by_email(db, "p41-multi@example.com").id)
    wf = _workflow(db, org)
    start = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    _execution(db, wf, status="COMPLETED", started=start,
               completed=start + timedelta(seconds=60))
    _execution(db, wf, status="COMPLETED", started=start,
               completed=start + timedelta(seconds=180))
    res = _analytics(client, headers, org)
    assert res.json()["average_execution_time"] == pytest.approx(120.0)


def test_average_execution_time_excludes_missing_end_timestamp(client, db):
    headers = _register(client, "p41-incomplete@example.com")
    org = _make_org(db, _user_by_email(db, "p41-incomplete@example.com").id)
    wf = _workflow(db, org)
    start = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    _execution(db, wf, status="COMPLETED", started=start,
               completed=start + timedelta(seconds=100))
    # Missing end timestamp -> excluded from the average
    _execution(db, wf, status="ACTIVE", started=start)
    _execution(db, wf, status="COMPLETED", started=start)  # completed but no end
    res = _analytics(client, headers, org)
    assert res.json()["average_execution_time"] == pytest.approx(100.0)


def test_missing_start_timestamp_is_schema_forbidden(client, db):
    """The schema declares started_at nullable=False, so a NULL start cannot
    exist in production. The service guard (e.started_at and e.completed_at)
    remains as defense in depth; here we pin the schema guarantee itself."""
    from sqlalchemy import inspect as sa_inspect
    from app.db.base import Base
    col = sa_inspect(Base.metadata.tables["workflow_executions"]).columns["started_at"]
    assert col.nullable is False


def test_average_execution_time_zero_when_no_valid_durations(client, db):
    headers = _register(client, "p41-nodurations@example.com")
    org = _make_org(db, _user_by_email(db, "p41-nodurations@example.com").id)
    wf = _workflow(db, org)
    start = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    _execution(db, wf, status="ACTIVE", started=start)  # no end
    _execution(db, wf, status="COMPLETED", started=start)  # no end
    res = _analytics(client, headers, org)
    assert res.json()["average_execution_time"] == 0.0


# ---------------------------------------------------------------------------
# blocked_executions
# ---------------------------------------------------------------------------

def test_blocked_execution_counted_for_pending_approval(client, db):
    headers = _register(client, "p41-blocked@example.com")
    org = _make_org(db, _user_by_email(db, "p41-blocked@example.com").id)
    wf = _workflow(db, org)
    ex = _execution(db, wf, status="ACTIVE")
    _pending_approval(db, wf, ex, status="PENDING")
    res = _analytics(client, headers, org)
    assert res.json()["blocked_executions"] == 1


def test_failed_executions_not_counted_as_blocked(client, db):
    headers = _register(client, "p41-failed@example.com")
    org = _make_org(db, _user_by_email(db, "p41-failed@example.com").id)
    wf = _workflow(db, org)
    ex = _execution(db, wf, status="FAILED")
    _pending_approval(db, wf, ex, status="PENDING")
    res = _analytics(client, headers, org)
    data = res.json()
    assert data["blocked_executions"] == 0
    assert data["failed_executions"] == 1


def test_resolved_approvals_do_not_block(client, db):
    headers = _register(client, "p41-resolved@example.com")
    org = _make_org(db, _user_by_email(db, "p41-resolved@example.com").id)
    wf = _workflow(db, org)
    ex = _execution(db, wf, status="ACTIVE")
    _pending_approval(db, wf, ex, status="APPROVED")
    res = _analytics(client, headers, org)
    assert res.json()["blocked_executions"] == 0


def test_active_execution_without_approval_not_blocked(client, db):
    headers = _register(client, "p41-running@example.com")
    org = _make_org(db, _user_by_email(db, "p41-running@example.com").id)
    wf = _workflow(db, org)
    _execution(db, wf, status="ACTIVE")
    res = _analytics(client, headers, org)
    assert res.json()["blocked_executions"] == 0


# ---------------------------------------------------------------------------
# Isolation / contract
# ---------------------------------------------------------------------------

def test_workflow_analytics_isolated_by_organization(client, db):
    headers_a = _register(client, "p41-owner@example.com")
    org_a = _make_org(db, _user_by_email(db, "p41-owner@example.com").id)
    wf = _workflow(db, org_a)
    start = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    _execution(db, wf, status="COMPLETED", started=start,
               completed=start + timedelta(seconds=42))

    headers_b = _register(client, "p41-outsider@example.com")
    org_b = _make_org(db, _user_by_email(db, "p41-outsider@example.com").id)

    res = _analytics(client, headers_b, org_b)
    data = res.json()
    assert data["executions"] == 0
    assert data["average_execution_time"] == 0.0
    assert data["blocked_executions"] == 0


def test_workflow_analytics_contract_shape(client, db):
    """Response must stay compatible with the existing schema contract."""
    headers = _register(client, "p41-contract@example.com")
    org = _make_org(db, _user_by_email(db, "p41-contract@example.com").id)
    _workflow(db, org)
    res = _analytics(client, headers, org)
    data = res.json()
    # Validates against the existing response model (extra/missing fields fail)
    WorkflowAnalyticsResponse(**data)
    assert set(data.keys()) == {
        "active_workflows", "executions", "success_rate", "failed_executions",
        "average_execution_time", "blocked_executions",
    }
