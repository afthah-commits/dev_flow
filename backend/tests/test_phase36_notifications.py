"""Phase 36 — Advanced Notifications & Action Center.

Covers:
- notification creation (service level + dedup/idempotency)
- listing, filtering, pagination (backend-driven)
- read / unread / mark-all-read
- important state
- summary counts
- action-center aggregation
- notification preferences
- RBAC (unauthenticated access)
- cross-user isolation
- cross-organization isolation
- ID manipulation (foreign notification ids)
- realtime event scoping (ConnectionManager user/org scope)
- preference gating of generated notifications
"""
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest

from app.models.notification import Notification, NotificationPreference, NotificationType
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.websockets.manager import ConnectionManager
from app.services.notification_service import (
    create_notification,
    get_preferences,
    notify_job_failure,
    notify_release_event,
    notify_automation_failure,
    notify_daily_report_blocker,
    notify_team_activity,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_from_stale_auth_overrides():
    """tests/api/v1/*.py register app.dependency_overrides[get_current_user]
    at module import time and never remove them, so any test collected after
    them silently bypasses authentication. Phase 36 tests assert on real RBAC,
    so they clear those leaked overrides for their own duration and restore
    them afterwards (leaving other suites exactly as they were).
    """
    from app.main import app as _app
    from app.api import deps as _deps
    keys = (_deps.get_current_user, _deps.get_current_organization_id)
    saved = {k: _app.dependency_overrides.pop(k) for k in keys if k in _app.dependency_overrides}
    yield
    _app.dependency_overrides.update(saved)


def _register(client, email, name="Phase36 User"):
    client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _make_user(db, uid, email=None):
    """Insert a real user row so FK-backed columns stay valid."""
    if db.query(User).filter(User.id == uid).first():
        return
    from app.core.security import get_password_hash
    db.add(User(id=uid, name="Phase36", email=email or f"{uid.hex[:12]}@p36.test",
                password_hash=get_password_hash("password123")))
    db.commit()


def _make_org(db, owner_id, slug=None):
    _make_user(db, owner_id)
    org = Organization(id=uuid4(), name=f"Org {slug or uuid4().hex[:6]}",
                       slug=slug or f"org-{uuid4().hex[:8]}", created_by=owner_id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=owner_id,
                              role=OrganizationRole.OWNER))
    db.commit()
    return org


def _user_by_email(db, email):
    return db.query(User).filter(User.email == email).first()


# ---------------------------------------------------------------------------
# creation + dedup / idempotency
# ---------------------------------------------------------------------------

def test_create_notification_and_deduplication(db):
    uid = uuid4()
    org = _make_org(db, uid)

    assert create_notification(db, uid, NotificationType.JOB_FAILURE,
                               "Job Failed", "boom", entity_type="JOB",
                               entity_id=uuid4(), organization_id=org.id) is True

    count_before = db.query(Notification).filter(
        Notification.user_id == uid, Notification.type == NotificationType.JOB_FAILURE).count()
    assert count_before == 1

    # same user + same type + SAME entity id -> deduplicated
    same_entity = db.query(Notification).filter(
        Notification.user_id == uid, Notification.type == NotificationType.JOB_FAILURE).first()
    create_notification(db, uid, NotificationType.JOB_FAILURE, "Job Failed", "boom",
                        entity_type="JOB", entity_id=same_entity.entity_id,
                        organization_id=org.id)
    db.expire_all()
    count_after = db.query(Notification).filter(
        Notification.user_id == uid, Notification.type == NotificationType.JOB_FAILURE).count()
    assert count_after == 1, "deduplication must prevent duplicate notifications for one event"


def test_create_notification_is_idempotent_return_value(db):
    uid = uuid4()
    org = _make_org(db, uid)
    entity = uuid4()

    first = create_notification(db, uid, NotificationType.RELEASE_PROMOTED,
                                "Release Promoted", "to staging",
                                entity_type="RELEASE", entity_id=entity,
                                organization_id=org.id)
    second = create_notification(db, uid, NotificationType.RELEASE_PROMOTED,
                                 "Release Promoted", "to staging",
                                 entity_type="RELEASE", entity_id=entity,
                                 organization_id=org.id)
    assert first is True
    assert second is None, "second identical event must be deduplicated (returns None)"


def test_different_users_get_their_own_notifications(db):
    ua, ub = uuid4(), uuid4()
    org = _make_org(db, ua)
    _make_user(db, ub)
    create_notification(db, ua, NotificationType.TEAM_ACTIVITY, "A", "a",
                        entity_type="TASK", entity_id=uuid4(), organization_id=org.id)
    create_notification(db, ub, NotificationType.TEAM_ACTIVITY, "B", "b",
                        entity_type="TASK", entity_id=uuid4(), organization_id=org.id)

    assert db.query(Notification).filter(Notification.user_id == ua).count() == 1
    assert db.query(Notification).filter(Notification.user_id == ub).count() == 1
    a_types = {n.title for n in db.query(Notification).filter(Notification.user_id == ua)}
    assert a_types == {"A"}


# ---------------------------------------------------------------------------
# preference gating
# ---------------------------------------------------------------------------

def test_preferences_gate_notification_generation(db):
    uid = uuid4()
    org = _make_org(db, uid)

    # default prefs allow job notifications -> one is created
    notify_job_failure(db, org.id, uuid4(), "thing", "err")
    db.expire_all()
    assert db.query(Notification).filter(
        Notification.user_id == uid, Notification.type == NotificationType.JOB_FAILURE).count() == 1

    # opt out -> no more
    pref = get_preferences(db, uid)
    pref.job_notifications = False
    db.commit()
    notify_job_failure(db, org.id, uuid4(), "other", "err")
    db.expire_all()
    assert db.query(Notification).filter(
        Notification.user_id == uid, Notification.type == NotificationType.JOB_FAILURE).count() == 1


def test_job_failure_skips_users_already_notified_for_same_job(db):
    """The scheduler writes its own JOB_FAILED notice; Phase 36 must not duplicate it."""
    uid = uuid4()
    org = _make_org(db, uid)
    job_id = uuid4()

    db.add(Notification(user_id=uid, organization_id=org.id, type="JOB_FAILED",
                        title="Job thing failed", message="legacy",
                        entity_type="job", entity_id=job_id))
    db.commit()

    notify_job_failure(db, org.id, job_id, "thing", "err")
    db.expire_all()

    assert db.query(Notification).filter(
        Notification.user_id == uid, Notification.entity_id == job_id).count() == 1


def test_daily_report_blocker_respects_preference(db):
    uid = uuid4()
    org = _make_org(db, uid)
    pref = get_preferences(db, uid)
    pref.daily_report_notifications = False
    db.commit()

    notify_daily_report_blocker(db, org.id, uuid4(), "Ann", ["blocked"])
    db.expire_all()
    assert db.query(Notification).filter(
        Notification.user_id == uid,
        Notification.type == NotificationType.DAILY_REPORT_BLOCKER).count() == 0

    pref.daily_report_notifications = True
    db.commit()
    notify_daily_report_blocker(db, org.id, uuid4(), "Ann", ["blocked"])
    db.expire_all()
    assert db.query(Notification).filter(
        Notification.user_id == uid,
        Notification.type == NotificationType.DAILY_REPORT_BLOCKER).count() == 1


def test_release_rollback_is_flagged_action_required_and_important(db):
    uid = uuid4()
    org = _make_org(db, uid)
    notify_release_event(db, org.id, uuid4(), "v1.2.3", "rollback")
    db.expire_all()
    n = db.query(Notification).filter(
        Notification.user_id == uid,
        Notification.type == NotificationType.RELEASE_ROLLBACK).first()
    assert n is not None
    assert n.action_required is True
    assert n.important is True


def test_team_activity_targets_only_the_recipient(db):
    org = _make_org(db, uuid4())
    recipient, bystander = uuid4(), uuid4()
    _make_user(db, recipient)
    _make_user(db, bystander)
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=bystander,
                              role=OrganizationRole.ADMIN))
    db.commit()

    notify_team_activity(db, org.id, recipient, "Task Assigned", "you got it",
                         "TASK", uuid4())
    db.expire_all()
    assert db.query(Notification).filter(Notification.user_id == recipient).count() == 1
    assert db.query(Notification).filter(Notification.user_id == bystander).count() == 0


def test_automation_failure_normalizes_string_ids(db):
    """Automation uses String-typed ids; notification storage must still work."""
    uid = uuid4()
    org = _make_org(db, uid)
    notify_automation_failure(db, str(org.id), str(uuid4()), "Nightly sync", "timeout")
    db.expire_all()
    assert db.query(Notification).filter(
        Notification.user_id == uid,
        Notification.type == NotificationType.AUTOMATION_FAILURE).count() == 1

    # non-UUID garbage must be a safe no-op, not an exception
    notify_automation_failure(db, "not-a-uuid", "not-a-uuid", "X", "y")
    assert True


# ---------------------------------------------------------------------------
# realtime scoping
# ---------------------------------------------------------------------------

class _FakeSocket:
    def __init__(self, name):
        self.name = name
        self.messages = []

    async def accept(self):
        pass

    async def send_json(self, message):
        self.messages.append(message)

    async def close(self, code=1000):
        pass


def test_notification_personal_message_targets_only_owner():
    m = ConnectionManager()
    owner, other = uuid4(), uuid4()
    ws_owner, ws_other = _FakeSocket("owner"), _FakeSocket("other")

    async def setup():
        await m.connect(ws_owner, uuid4(), owner)
        await m.connect(ws_other, uuid4(), other)
        await m.send_personal_message({"type": "notification.created", "n": 1}, owner)
    asyncio.run(setup())

    assert len(ws_owner.messages) == 1
    assert ws_other.messages == []


def test_action_item_broadcast_is_org_scoped():
    m = ConnectionManager()
    org_a, org_b = uuid4(), uuid4()
    ws_a, ws_b = _FakeSocket("a"), _FakeSocket("b")

    async def setup():
        await m.connect(ws_a, org_a, uuid4())
        await m.connect(ws_b, org_b, uuid4())
        await m.broadcast_to_org(org_a, {"type": "action_item.created", "n": 1})
    asyncio.run(setup())

    assert len(ws_a.messages) == 1
    assert ws_b.messages == []


# ---------------------------------------------------------------------------
# API: RBAC, listing, filters, pagination, state, summary, action center
# ---------------------------------------------------------------------------

def test_notifications_require_authentication(client):
    assert client.get("/api/v1/notifications").status_code == 401
    assert client.get("/api/v1/notifications/unread-count").status_code == 401
    assert client.get("/api/v1/notifications/summary").status_code == 401
    assert client.get("/api/v1/notifications/action-center").status_code == 401
    assert client.post("/api/v1/notifications/read-all").status_code == 401


def test_listing_pagination_and_backend_filters(client, db):
    headers = _register(client, "p36-list@example.com")
    user = _user_by_email(db, "p36-list@example.com")
    org = _make_org(db, user.id)

    for i in range(12):
        create_notification(db, user.id,
                            NotificationType.JOB_FAILURE if i % 2 == 0 else NotificationType.TEAM_ACTIVITY,
                            f"N{i}", f"msg {i}", entity_type="JOB",
                            entity_id=uuid4(), organization_id=org.id,
                            important=(i == 0), action_required=(i == 1))
    db.expire_all()

    page1 = client.get("/api/v1/notifications?limit=5&skip=0", headers=headers).json()
    assert len(page1) == 5

    page2 = client.get("/api/v1/notifications?limit=5&skip=5", headers=headers).json()
    assert len(page2) == 5
    assert {n["id"] for n in page1}.isdisjoint({n["id"] for n in page2})

    total = client.get("/api/v1/notifications?limit=200", headers=headers).json()
    assert len(total) >= 12

    # type filter is applied in SQL, not client-side
    typed = client.get(
        "/api/v1/notifications?notification_type=JOB_FAILURE&limit=200", headers=headers).json()
    assert typed and all(n["type"] == "JOB_FAILURE" for n in typed)

    # important / action_required filters
    imp = client.get("/api/v1/notifications?important=true&limit=200", headers=headers).json()
    assert imp and all(n["important"] for n in imp)

    act = client.get("/api/v1/notifications?action_required=true&limit=200", headers=headers).json()
    assert act and all(n["action_required"] for n in act)

    # unread-only filter
    unread = client.get("/api/v1/notifications?unread_only=true&limit=200", headers=headers).json()
    assert unread and all(n["read"] is False for n in unread)

    # date range filter (date-only values, no timezone offsets to URL-encode)
    none_in_future = client.get(
        "/api/v1/notifications?date_from=2099-01-01T00:00:00&limit=200", headers=headers).json()
    assert none_in_future == [], f"future date_from must return no rows, got {none_in_future}"

    all_in_past = client.get(
        "/api/v1/notifications?date_from=2000-01-01T00:00:00&limit=200", headers=headers).json()
    assert len(all_in_past) >= 12


def test_read_unread_mark_all_and_important_flow(client, db):
    headers = _register(client, "p36-state@example.com")
    user = _user_by_email(db, "p36-state@example.com")
    org = _make_org(db, user.id)

    create_notification(db, user.id, NotificationType.TEAM_ACTIVITY, "One", "m1",
                        entity_type="TASK", entity_id=uuid4(), organization_id=org.id)
    create_notification(db, user.id, NotificationType.TEAM_ACTIVITY, "Two", "m2",
                        entity_type="TASK", entity_id=uuid4(), organization_id=org.id)
    db.expire_all()

    assert client.get("/api/v1/notifications/unread-count", headers=headers).json()["count"] == 2

    listing = client.get("/api/v1/notifications?limit=200", headers=headers).json()
    first, second = listing[0], listing[1]

    # mark read
    res = client.patch(f"/api/v1/notifications/{first['id']}/read", headers=headers)
    assert res.status_code == 200
    assert res.json()["read"] is True
    assert res.json()["read_at"] is not None
    assert client.get("/api/v1/notifications/unread-count", headers=headers).json()["count"] == 1

    # mark unread again
    res = client.patch(f"/api/v1/notifications/{first['id']}/unread", headers=headers)
    assert res.status_code == 200
    assert res.json()["read"] is False
    assert res.json()["read_at"] is None
    assert client.get("/api/v1/notifications/unread-count", headers=headers).json()["count"] == 2

    # important / unimportant
    res = client.patch(f"/api/v1/notifications/{first['id']}/important", headers=headers)
    assert res.status_code == 200 and res.json()["important"] is True
    res = client.patch(f"/api/v1/notifications/{first['id']}/unimportant", headers=headers)
    assert res.status_code == 200 and res.json()["important"] is False

    # mark all read
    res = client.post("/api/v1/notifications/read-all", headers=headers)
    assert res.status_code == 200
    assert client.get("/api/v1/notifications/unread-count", headers=headers).json()["count"] == 0

    # mark all read is idempotent
    assert client.post("/api/v1/notifications/read-all", headers=headers).status_code == 200
    assert client.get("/api/v1/notifications/unread-count", headers=headers).json()["count"] == 0

    # delete
    res = client.delete(f"/api/v1/notifications/{second['id']}", headers=headers)
    assert res.status_code == 200
    remaining = client.get("/api/v1/notifications?limit=200", headers=headers).json()
    assert second["id"] not in [n["id"] for n in remaining]


def test_summary_counts(client, db):
    headers = _register(client, "p36-summary@example.com")
    user = _user_by_email(db, "p36-summary@example.com")
    org = _make_org(db, user.id)

    create_notification(db, user.id, NotificationType.TEAM_ACTIVITY, "unread+important",
                        "m", entity_type="TASK", entity_id=uuid4(),
                        organization_id=org.id, important=True, action_required=True)
    create_notification(db, user.id, NotificationType.JOB_FAILURE, "read me", "m",
                        entity_type="JOB", entity_id=uuid4(), organization_id=org.id)
    db.expire_all()

    listing = client.get("/api/v1/notifications?limit=200", headers=headers).json()
    to_read = [n for n in listing if not n["read"]][0]
    client.patch(f"/api/v1/notifications/{to_read['id']}/read", headers=headers)

    s = client.get("/api/v1/notifications/summary", headers=headers).json()
    assert s["unread"] == 1
    assert s["important"] == 1
    assert s["action_required"] == 1
    assert s["pending_approvals"] == 0
    assert s["failed_jobs"] == 0
    assert isinstance(s["failed_jobs"], int)


def test_action_center_aggregates_and_is_user_scoped(client, db):
    headers_a = _register(client, "p36-act-a@example.com")
    headers_b = _register(client, "p36-act-b@example.com")
    user_a = _user_by_email(db, "p36-act-a@example.com")
    org_a = _make_org(db, user_a.id)

    # an action-required notification for user A shows up in A's action center
    create_notification(db, user_a.id, NotificationType.DAILY_REPORT_BLOCKER,
                        "Daily Report Blocker", "2 blockers",
                        entity_type="DAILY_REPORT", entity_id=uuid4(),
                        organization_id=org_a.id, action_required=True)
    db.expire_all()

    items_a = client.get("/api/v1/notifications/action-center", headers=headers_a).json()
    assert isinstance(items_a, list)
    assert any(i["type"] == "NOTIFICATION" for i in items_a)
    for i in items_a:
        assert {"id", "type", "title", "description", "entity_type", "priority", "created_at"} <= set(i)

    # user B must not see user A's action items
    items_b = client.get("/api/v1/notifications/action-center", headers=headers_b).json()
    assert all(i["title"] != "Daily Report Blocker" for i in items_b)

    # items are ordered by priority (URGENT/HIGH first)
    order = {"URGENT": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}
    priorities = [order.get(i["priority"], 2) for i in items_a]
    assert priorities == sorted(priorities)


def test_cross_user_id_manipulation_returns_404(client, db):
    headers_a = _register(client, "p36-xuser-a@example.com")
    headers_b = _register(client, "p36-xuser-b@example.com")
    user_a = _user_by_email(db, "p36-xuser-a@example.com")
    org = _make_org(db, user_a.id)

    create_notification(db, user_a.id, NotificationType.TEAM_ACTIVITY, "Private", "m",
                        entity_type="TASK", entity_id=uuid4(), organization_id=org.id)
    db.expire_all()
    foreign_id = db.query(Notification).filter(
        Notification.user_id == user_a.id).first().id

    for method, url in [
        ("get", f"/api/v1/notifications/{foreign_id}"),
        ("patch", f"/api/v1/notifications/{foreign_id}/read"),
        ("patch", f"/api/v1/notifications/{foreign_id}/unread"),
        ("patch", f"/api/v1/notifications/{foreign_id}/important"),
        ("patch", f"/api/v1/notifications/{foreign_id}/unimportant"),
        ("delete", f"/api/v1/notifications/{foreign_id}"),
    ]:
        res = getattr(client, method)(url, headers=headers_b)
        assert res.status_code == 404, f"{method} {url} must not leak another user's notification"

    # user A still owns it
    assert client.get(f"/api/v1/notifications/{foreign_id}",
                      headers=headers_a).status_code == 200


def test_malformed_and_random_ids_are_rejected_not_500(client, db):
    headers = _register(client, "p36-badid@example.com")
    for url in ["/api/v1/notifications/not-a-uuid",
                "/api/v1/notifications/00000000-0000-0000-0000-000000000000"]:
        assert client.get(url, headers=headers).status_code in (404, 422)
        assert client.patch(f"{url}/read", headers=headers).status_code in (404, 422)
        assert client.delete(url, headers=headers).status_code in (404, 422)


def test_preferences_roundtrip(client, db):
    headers = _register(client, "p36-prefs@example.com")

    prefs = client.get("/api/v1/notifications/preferences", headers=headers).json()
    assert prefs["daily_report_notifications"] is True
    assert prefs["release_notifications"] is True
    assert prefs["team_activity_notifications"] is True

    res = client.patch("/api/v1/notifications/preferences", json={
        "task_notifications": False,
        "daily_report_notifications": False,
        "release_notifications": True,
        "team_activity_notifications": False,
    }, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["task_notifications"] is False
    assert body["daily_report_notifications"] is False
    assert body["team_activity_notifications"] is False
    assert body["release_notifications"] is True

    # persisted across requests
    again = client.get("/api/v1/notifications/preferences", headers=headers).json()
    assert again["daily_report_notifications"] is False


def test_notification_types_are_deterministic_and_supported(client):
    """Every Phase 36 category named in the spec exists as a constant."""
    required = [
        "DAILY_REPORT_REMINDER", "DAILY_REPORT_BLOCKER",
        "RELEASE_APPROVAL_REQUESTED", "RELEASE_APPROVED", "RELEASE_REJECTED",
        "RELEASE_PROMOTED", "RELEASE_ROLLBACK",
        "DEPLOYMENT_STARTED", "DEPLOYMENT_SUCCESS", "DEPLOYMENT_FAILED",
        "DEPLOYMENT_ROLLBACK",
        "JOB_FAILURE", "AUTOMATION_FAILURE",
        "WORKFLOW_APPROVAL_REQUESTED", "WORKFLOW_APPROVED", "WORKFLOW_REJECTED",
        "CLIENT_REQUEST_CREATED", "CLIENT_REQUEST_UPDATED",
        "TEAM_ACTIVITY",
    ]
    for t in required:
        assert hasattr(NotificationType, t), f"missing notification type {t}"
        assert getattr(NotificationType, t) == t


def test_action_center_aggregates_all_six_sources(client, db):
    """Every aggregation source must actually yield an item.

    The endpoint wraps each source in try/except, so a silent model mismatch
    (e.g. using a non-existent Deployment.name) would look like an empty list
    rather than an error. This pins all six sources in the permanent suite.
    """
    from datetime import datetime, timezone as tz
    from uuid import uuid4 as _u4
    from app.models.workflow import (
        Workflow, WorkflowState, WorkflowTransition,
        WorkflowApproval, WorkflowApprovalStatus,
    )
    from app.models.delivery import (
        Release, ReleaseApproval, ReleaseApprovalStatus,
        Deployment, DeploymentStatus,
    )
    from app.models.job import Job
    from app.models.daily_report import DailyReport
    from app.models.project import Project

    headers = _register(client, "p36-all-sources@example.com")
    user = _user_by_email(db, "p36-all-sources@example.com")
    org = _make_org(db, user.id)
    now = datetime.now(tz.utc)

    # workflow approval (needs a real transition for its FK)
    wf = Workflow(id=_u4(), organization_id=org.id, name="P36 WF")
    db.add(wf); db.flush()
    s1 = WorkflowState(id=_u4(), workflow_id=wf.id, name="Start", key="start",
                       state_type="INITIAL", is_initial=True)
    s2 = WorkflowState(id=_u4(), workflow_id=wf.id, name="End", key="end",
                       state_type="FAILED", is_terminal=True)
    db.add_all([s1, s2]); db.flush()
    tr = WorkflowTransition(id=_u4(), workflow_id=wf.id, name="advance",
                            from_state_id=s1.id, to_state_id=s2.id,
                            requires_approval=True)
    db.add(tr); db.flush()
    db.add(WorkflowApproval(id=_u4(), workflow_transition_id=tr.id,
                            entity_type="TASK", entity_id=_u4(),
                            approver_user_id=user.id,
                            status=WorkflowApprovalStatus.PENDING,
                            requested_at=now))

    # release approval
    proj = Project(id=_u4(), name="P36 Proj", slug="p36-proj",
                   organization_id=org.id, owner_id=user.id)
    db.add(proj); db.flush()
    rel = Release(id=_u4(), organization_id=org.id, project_id=proj.id,
                  name="v1.0.0", version="1.0.0")
    db.add(rel); db.flush()
    db.add(ReleaseApproval(id=_u4(), organization_id=org.id, release_id=rel.id,
                           requested_by_id=user.id, reviewer_id=user.id,
                           status=ReleaseApprovalStatus.PENDING, created_at=now))

    # failed job
    db.add(Job(id=_u4(), organization_id=org.id, job_type="p36.probe",
               status="FAILED", attempts=3, max_attempts=3,
               error_message="boom", failed_at=now, created_at=now))

    # failed deployment (Deployment has no name/updated_at columns)
    db.add(Deployment(id=_u4(), organization_id=org.id, project_id=proj.id,
                      status=DeploymentStatus.FAILED, deployment_key="deploy-42",
                      error_message="exit 1", created_at=now))

    # daily report with blockers
    db.add(DailyReport(id=_u4(), organization_id=org.id, author_user_id=user.id,
                       report_date=now.date(), completed_tasks=["x"],
                       next_plan=["y"], blockers=["waiting on infra"]))

    # action-required notification
    create_notification(db, user.id, NotificationType.DAILY_REPORT_BLOCKER,
                        "Daily Report Blocker", "2 blockers",
                        entity_type="DAILY_REPORT", entity_id=_u4(),
                        organization_id=org.id, action_required=True)
    db.expire_all()

    items = client.get("/api/v1/notifications/action-center", headers=headers).json()
    types = {i["type"] for i in items}

    expected = {
        "WORKFLOW_APPROVAL", "RELEASE_APPROVAL", "JOB_FAILURE",
        "DEPLOYMENT_FAILURE", "DAILY_REPORT_BLOCKER", "NOTIFICATION",
    }
    assert expected <= types, f"missing action items for: {expected - types}"

    dep = [i for i in items if i["type"] == "DEPLOYMENT_FAILURE"][0]
    assert "deploy-42" in dep["description"], \
        "deployment label must come from deployment_key, not a nonexistent name column"
    for i in items:
        assert i["created_at"], f"{i['type']} must carry created_at"


def test_all_phase36_notification_rows_carry_organization_scope(db):
    """Rows generated for org events must record their organization_id."""
    uid = uuid4()
    org = _make_org(db, uid)
    notify_release_event(db, org.id, uuid4(), "v1", "promoted", "staging")
    notify_job_failure(db, org.id, uuid4(), "t", "e")
    db.expire_all()

    rows = db.query(Notification).filter(Notification.user_id == uid).all()
    assert rows
    assert all(r.organization_id == org.id for r in rows)


# ---------------------------------------------------------------------------
# GlobalSearch integration
# ---------------------------------------------------------------------------

def test_global_search_finds_own_notifications_only(client, db):
    headers_a = _register(client, "p36-search-a@example.com")
    headers_b = _register(client, "p36-search-b@example.com")
    user_a = _user_by_email(db, "p36-search-a@example.com")
    org_a = _make_org(db, user_a.id)

    create_notification(db, user_a.id, NotificationType.DAILY_REPORT_REMINDER,
                        "Quarterly zebra report reminder",
                        "you have not submitted a zebra report",
                        entity_type="DAILY_REPORT", entity_id=uuid4(),
                        organization_id=org_a.id)
    db.expire_all()

    res = client.get("/api/v1/search?q=zebra",
                     headers={**headers_a, "X-Organization-Id": str(org_a.id)})
    assert res.status_code == 200
    hits = [r for r in res.json() if r["entity_type"] == "NOTIFICATION"]
    assert hits, "own notifications must be searchable"
    assert hits[0]["url"] == "/notifications"

    # another user (in their own org) must never see them
    user_b = _user_by_email(db, "p36-search-b@example.com")
    org_b = _make_org(db, user_b.id)
    res_b = client.get("/api/v1/search?q=zebra",
                       headers={**headers_b, "X-Organization-Id": str(org_b.id)})
    assert res_b.status_code == 200
    assert not [r for r in res_b.json() if r["entity_type"] == "NOTIFICATION"]
