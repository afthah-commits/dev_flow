"""Phase 31 — background job platform validation (Phase 23 job scheduler).

Covers: QUEUED -> RUNNING -> SUCCESS, retry with exponential backoff,
permanent failure (audit + OWNER/ADMIN notifications — exercises the Phase 31
Notification schema fix), stuck-RUNNING timeout recovery, idempotency-key
integrity, and organization-scoped job listing.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.jobs import job_registry
from app.jobs.scheduler import scheduler
from app.models.audit import AuditEvent
from app.models.job import Job, JobExecution
from app.models.notification import Notification
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.user import User


@pytest.fixture
def auth_setup(db: Session):
    """OWNER user + organization for job tests (unique email per run)."""
    user = User(id=uuid.uuid4(), name="P31 User",
                email=f"p31_{uuid.uuid4().hex[:8]}@test.com", password_hash="pwd")
    org = Organization(id=uuid.uuid4(), name=f"P31 Org {uuid.uuid4().hex[:6]}",
                       slug=f"p31-{uuid.uuid4().hex[:8]}", created_by=user.id)
    db.add(user)
    db.commit()
    db.add(org)
    db.commit()
    db.add(OrganizationMember(organization_id=org.id, user_id=user.id,
                              role=OrganizationRole.OWNER))
    db.commit()
    token = create_access_token(user.id)
    return {
        "headers": {"Authorization": f"Bearer {token}",
                    "X-Organization-Id": str(org.id)},
        "org_id": org.id,
        "user_id": user.id,
    }


@pytest.fixture
def second_org(db: Session):
    """A separate ORG-B with its own OWNER (for isolation tests)."""
    user = User(id=uuid.uuid4(), name="P31 User B",
                email=f"p31b_{uuid.uuid4().hex[:8]}@test.com", password_hash="pwd")
    org = Organization(id=uuid.uuid4(), name=f"P31 Org B {uuid.uuid4().hex[:6]}",
                       slug=f"p31b-{uuid.uuid4().hex[:8]}", created_by=user.id)
    db.add(user)
    db.commit()
    db.add(org)
    db.commit()
    db.add(OrganizationMember(organization_id=org.id, user_id=user.id,
                              role=OrganizationRole.OWNER))
    db.commit()
    token = create_access_token(user.id)
    return {
        "headers": {"Authorization": f"Bearer {token}",
                    "X-Organization-Id": str(org.id)},
        "org_id": org.id,
        "user_id": user.id,
    }


def _make_job(db: Session, org_id, **kwargs) -> Job:
    job = Job(
        organization_id=org_id,
        job_type=kwargs.pop("job_type", "phase31.test"),
        **kwargs,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _audit_types(db: Session, job_id) -> list:
    rows = db.query(AuditEvent).filter(AuditEvent.entity_id == job_id).all()
    return [e.event_type for e in rows]


def _seconds_from_now(dt) -> float:
    """SQLite returns naive datetimes; treat them as UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt - datetime.now(timezone.utc)).total_seconds()


# ---------------------------------------------------------------------------
# State machine: QUEUED -> RUNNING -> SUCCESS
# ---------------------------------------------------------------------------

def test_job_success_flow(client: TestClient, db: Session, auth_setup):
    org_id = auth_setup["org_id"]
    job_registry.register("phase31.ok", lambda payload: None)
    job = _make_job(db, org_id, job_type="phase31.ok")

    scheduler.execute_job(db, job)
    db.refresh(job)

    assert job.status == "SUCCESS"
    assert job.attempts == 1
    assert job.completed_at is not None
    assert job.error_message is None

    execution = db.query(JobExecution).filter(JobExecution.job_id == job.id).one()
    assert execution.status == "SUCCESS"

    events = _audit_types(db, job.id)
    assert "job.started" in events
    assert "job.completed" in events


# ---------------------------------------------------------------------------
# Retry with exponential backoff
# ---------------------------------------------------------------------------

def test_job_failure_retries_with_exponential_backoff(client: TestClient, db: Session, auth_setup):
    org_id = auth_setup["org_id"]

    def boom(payload):
        raise RuntimeError("kaboom")

    job_registry.register("phase31.flaky", boom)
    job = _make_job(db, org_id, job_type="phase31.flaky", max_attempts=3)

    # Attempt 1 -> RETRYING after 2^1 * 10 = 20s
    scheduler.execute_job(db, job)
    db.refresh(job)
    assert job.status == "RETRYING"
    assert job.attempts == 1
    first_delay = _seconds_from_now(job.scheduled_at)
    assert 10 <= first_delay <= 25, f"unexpected first backoff: {first_delay}"

    # Attempt 2 -> RETRYING after 2^2 * 10 = 40s (backoff grows)
    job.scheduled_at = None  # make it eligible now
    db.commit()
    scheduler.execute_job(db, job)
    db.refresh(job)
    assert job.status == "RETRYING"
    assert job.attempts == 2
    second_delay = _seconds_from_now(job.scheduled_at)
    assert second_delay > first_delay, "backoff must grow exponentially"
    assert 30 <= second_delay <= 45, f"unexpected second backoff: {second_delay}"

    events = _audit_types(db, job.id)
    assert "job.failed" in events
    assert "job.permanently_failed" not in events

    executions = db.query(JobExecution).filter(JobExecution.job_id == job.id).all()
    assert [e.status for e in executions] == ["FAILED", "FAILED"]


# ---------------------------------------------------------------------------
# Permanent failure: audit + OWNER/ADMIN notifications (Phase 31 fix)
# ---------------------------------------------------------------------------

def test_job_permanent_failure_notifies_org_admins(client: TestClient, db: Session, auth_setup):
    org_id = auth_setup["org_id"]
    owner_id = auth_setup["user_id"]

    def boom(payload):
        raise RuntimeError("permanent boom")

    job_registry.register("phase31.always_fails", boom)
    # attempts will be incremented to 1, which already meets max_attempts=1
    job = _make_job(db, org_id, job_type="phase31.always_fails", max_attempts=1)

    scheduler.execute_job(db, job)
    db.refresh(job)

    assert job.status == "FAILED"
    assert job.failed_at is not None

    events = _audit_types(db, job.id)
    assert "job.permanently_failed" in events

    # The org OWNER receives a JOB_FAILED notification (previously this
    # crashed the scheduler with invalid Notification columns)
    note = db.query(Notification).filter(
        Notification.user_id == owner_id,
        Notification.type == "JOB_FAILED",
        Notification.entity_id == job.id,
    ).first()
    assert note is not None, "permanent failure must notify org admins"
    assert "phase31.always_fails" in note.title
    assert note.message


# ---------------------------------------------------------------------------
# Stuck RUNNING job timeout recovery (uses its own SessionLocal session)
# ---------------------------------------------------------------------------

def test_stuck_running_job_recovered_as_timed_out():
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.models.organization import Organization

    db = SessionLocal()
    try:
        user = User(id=uuid.uuid4(), name="Stuck User",
                    email=f"stuck_{uuid.uuid4().hex[:8]}@test.com", password_hash="x")
        db.add(user)
        db.flush()
        org = Organization(id=uuid.uuid4(), name="Stuck Org",
                           slug=f"stuck-{uuid.uuid4().hex[:8]}", created_by=user.id)
        db.add(org)
        db.flush()
        stuck = Job(
            organization_id=org.id, job_type="phase31.stuck", status="RUNNING",
            started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        db.add(stuck)
        db.commit()
        stuck_id = stuck.id

        scheduler.process_jobs()

        db.expire_all()
        recovered = db.query(Job).filter(Job.id == stuck_id).one()
        assert recovered.status == "FAILED"
        assert recovered.error_message == "Job timed out"
        execution = db.query(JobExecution).filter(JobExecution.job_id == stuck_id).one()
        assert execution.status == "FAILED"
        assert "recovered by scheduler" in (execution.error_message or "")
    finally:
        # cleanup committed rows
        try:
            db.query(JobExecution).filter(
                JobExecution.job_id.in_(db.query(Job.id).filter(Job.job_type == "phase31.stuck"))
            ).delete(synchronize_session=False)
            db.query(Job).filter(Job.job_type == "phase31.stuck").delete(synchronize_session=False)
            db.query(Organization).filter(Organization.name == "Stuck Org").delete(synchronize_session=False)
            db.query(User).filter(User.email.like("stuck_%@test.com")).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Idempotency key integrity
# ---------------------------------------------------------------------------

def test_job_idempotency_key_unique(client: TestClient, db: Session, auth_setup):
    from sqlalchemy.exc import IntegrityError

    org_id = auth_setup["org_id"]
    key = f"idem-{uuid.uuid4().hex[:12]}"
    _make_job(db, org_id, idempotency_key=key)

    duplicate = Job(organization_id=org_id, job_type="phase31.test", idempotency_key=key)
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


# ---------------------------------------------------------------------------
# Organization-scoped job listing (API)
# ---------------------------------------------------------------------------

def test_job_listing_is_organization_scoped(client: TestClient, db: Session, auth_setup, second_org):
    headers_b = second_org["headers"]
    org_b = second_org["org_id"]

    # A job exists in ORG-A (this test's auth_setup org)
    job_a = _make_job(db, auth_setup["org_id"], job_type="phase31.secret")

    res = client.get("/api/v1/jobs", headers=headers_b)
    assert res.status_code == 200
    jobs = res.json()
    items = jobs["items"] if isinstance(jobs, dict) else jobs
    assert all(j["id"] != str(job_a.id) for j in items), \
        "ORG-B must never see ORG-A jobs"

    # And ORG-A sees its own
    res = client.get("/api/v1/jobs", headers=auth_setup["headers"])
    assert res.status_code == 200
    jobs = res.json()
    items = jobs["items"] if isinstance(jobs, dict) else jobs
    assert any(j["id"] == str(job_a.id) for j in items)


# ---------------------------------------------------------------------------
# Missing handler fails the job safely (no crash)
# ---------------------------------------------------------------------------

def test_job_with_unknown_handler_fails_safely(client: TestClient, db: Session, auth_setup):
    job = _make_job(db, auth_setup["org_id"], job_type="phase31.no_such_handler")
    scheduler.execute_job(db, job)
    db.refresh(job)
    assert job.status == "FAILED"
    assert "No handler registered" in (job.error_message or "")
