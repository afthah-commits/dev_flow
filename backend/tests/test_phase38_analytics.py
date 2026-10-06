"""Phase 38 — Analytics platform consolidation & reliability.

Covers:
- single authoritative route per analytics endpoint (no shadowing)
- /analytics/delivery returns the complete DeliveryMetrics shape (incl.
  pipeline_success_rate) and supports the project_id filter
- /analytics/dora contract
- auth (401), org membership (403), RBAC and tenant isolation on analytics
- status_distribution list shape and deadline bucketing from Phase 37 fixes
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.delivery import (
    Release, ReleaseStatus, Deployment, DeploymentStatus, PipelineRun, PipelineStatus,
)

ANALYTICS_ORG_PATHS = [
    "/api/v1/analytics/dashboard",
    "/api/v1/analytics/executive",
    "/api/v1/analytics/delivery",
    "/api/v1/analytics/dora",
    "/api/v1/analytics/productivity",
    "/api/v1/analytics/workflow",
    "/api/v1/analytics/automation",
    "/api/v1/analytics/clients",
    "/api/v1/analytics/knowledge",
    "/api/v1/analytics/collaboration",
    "/api/v1/analytics/usage",
]


def _register(client, email, name="P38 User"):
    client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _make_user(db, uid, email=None):
    if db.query(User).filter(User.id == uid).first():
        return
    from app.core.security import get_password_hash
    db.add(User(id=uid, name="P38", email=email or f"{uid.hex[:12]}@p38.test",
                password_hash=get_password_hash("password123")))
    db.commit()


def _make_org(db, owner_id, slug=None):
    _make_user(db, owner_id)
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=slug or f"p38-{uuid4().hex[:8]}", created_by=owner_id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=owner_id,
                              role=OrganizationRole.OWNER))
    db.commit()
    return org


# ---------------------------------------------------------------------------
# Router consolidation: exactly one authoritative route
# ---------------------------------------------------------------------------

def test_no_duplicate_routes_anywhere_in_app():
    from app.main import app
    from collections import Counter
    seen = [(getattr(r, "path", ""), tuple(sorted(getattr(r, "methods", []) or [])))
            for r in app.routes if hasattr(r, "methods")]
    dups = [p for p, c in Counter(seen).items() if c > 1]
    assert not dups, f"duplicate routes: {dups}"


def test_delivery_and_dora_registered_on_analytics_router():
    from app.main import app
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/v1/analytics/delivery" in paths
    assert "/api/v1/analytics/dora" in paths


# ---------------------------------------------------------------------------
# Auth / RBAC / tenant isolation across every analytics org endpoint
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", ANALYTICS_ORG_PATHS)
def test_analytics_endpoints_require_authentication(client, path):
    assert client.get(path).status_code == 401, f"{path} must reject unauthenticated access"


@pytest.mark.parametrize("path", ANALYTICS_ORG_PATHS)
def test_analytics_endpoints_require_org_header(client, path):
    headers = _register(client, f"p38-noorg-{abs(hash(path)) % 9999}@example.com")
    res = client.get(path, headers=headers)
    assert res.status_code in (400, 403), \
        f"{path} must not serve org data without an organization context"


def test_analytics_rejects_non_member_with_foreign_org_header(client, db):
    headers = _register(client, "p38-foreign@example.com")
    other = _make_org(db, uuid4())  # org the caller does not belong to
    for path in ["/api/v1/analytics/dashboard", "/api/v1/analytics/executive",
                 "/api/v1/analytics/delivery", "/api/v1/analytics/dora"]:
        res = client.get(path, headers={**headers, "X-Organization-Id": str(other.id)})
        assert res.status_code == 403, f"{path} must reject a non-member (got {res.status_code})"


def test_analytics_member_can_read_own_org(client, db):
    headers = _register(client, "p38-member@example.com")
    user = db.query(User).filter(User.email == "p38-member@example.com").first()
    org = _make_org(db, user.id)
    h = {**headers, "X-Organization-Id": str(org.id)}

    for path in ["/api/v1/analytics/dashboard", "/api/v1/analytics/executive",
                 "/api/v1/analytics/delivery", "/api/v1/analytics/dora",
                 "/api/v1/analytics/workflow", "/api/v1/analytics/usage"]:
        res = client.get(path, headers=h)
        assert res.status_code == 200, f"{path} failed: {res.status_code} {res.text[:200]}"


def test_delivery_metrics_shape_matches_frontend_contract(client, db):
    """Frontend DeliveryAnalytics.tsx calls .toFixed on these numeric fields."""
    headers = _register(client, "p38-shape@example.com")
    user = db.query(User).filter(User.email == "p38-shape@example.com").first()
    org = _make_org(db, user.id)
    h = {**headers, "X-Organization-Id": str(org.id)}

    # seed one successful deployment so the endpoint has data
    proj = Project(id=uuid4(), name="P38 Proj", slug="p38-shape-proj",
                   organization_id=org.id, owner_id=user.id)
    db.add(proj)
    db.flush()
    db.add(Deployment(id=uuid4(), organization_id=org.id, project_id=proj.id,
                      status=DeploymentStatus.SUCCESS, duration_seconds=120,
                      created_at=datetime.now(timezone.utc)))
    db.commit()

    res = client.get("/api/v1/analytics/delivery", headers=h)
    assert res.status_code == 200
    data = res.json()
    numeric = ["deployment_frequency", "successful_deployment_rate", "failed_deployment_rate",
               "avg_deployment_duration_seconds", "release_frequency",
               "avg_release_cycle_time_days", "pipeline_success_rate",
               "rollback_frequency", "avg_lead_time_days"]
    for key in numeric:
        assert key in data, f"missing DeliveryMetrics field {key}"
        assert isinstance(data[key], (int, float)), f"{key} must be numeric, got {type(data[key])}"

    # project_id filter keeps the response within the org's data
    res2 = client.get(f"/api/v1/analytics/delivery?project_id={proj.id}", headers=h)
    assert res2.status_code == 200
    assert res2.json()["deployment_frequency"] == 1


def test_delivery_metrics_never_leaks_other_orgs_deployments(client, db):
    headers_a = _register(client, "p38-iso-a@example.com")
    headers_b = _register(client, "p38-iso-b@example.com")
    user_a = db.query(User).filter(User.email == "p38-iso-a@example.com").first()
    org_a = _make_org(db, user_a.id)

    proj = Project(id=uuid4(), name="A proj", slug="p38-iso-a-proj",
                   organization_id=org_a.id, owner_id=user_a.id)
    db.add(proj)
    db.flush()
    db.add(Deployment(id=uuid4(), organization_id=org_a.id, project_id=proj.id,
                      status=DeploymentStatus.FAILED, created_at=datetime.now(timezone.utc)))
    db.commit()

    res_a = client.get("/api/v1/analytics/delivery", headers={
        **headers_a, "X-Organization-Id": str(org_a.id)})
    assert res_a.json()["deployment_frequency"] == 1

    # user B, in their own deployment-free org, must see zero — a leaked
    # count would be 1
    user_b = db.query(User).filter(User.email == "p38-iso-b@example.com").first()
    org_b = _make_org(db, user_b.id)
    res_b = client.get("/api/v1/analytics/delivery", headers={
        **headers_b, "X-Organization-Id": str(org_b.id)})
    assert res_b.status_code == 200
    assert res_b.json()["deployment_frequency"] == 0, \
        "delivery analytics must not leak another org's deployments"


def test_project_analytics_scoped_and_typed(client, db):
    headers = _register(client, "p38-proj@example.com")
    user = db.query(User).filter(User.email == "p38-proj@example.com").first()
    org = _make_org(db, user.id)
    proj = Project(id=uuid4(), name="P38 PA", slug="p38-pa",
                   organization_id=org.id, owner_id=user.id)
    db.add(proj)
    db.flush()
    now = datetime.now(timezone.utc)
    db.add(Task(id=uuid4(), project_id=proj.id, title="done", status=TaskStatus.DONE,
                creator_id=user.id))
    db.add(Task(id=uuid4(), project_id=proj.id, title="soon",
                status=TaskStatus.TODO, creator_id=user.id,
                due_date=(now + timedelta(days=2))))
    db.add(Task(id=uuid4(), project_id=proj.id, title="far",
                status=TaskStatus.TODO, creator_id=user.id,
                due_date=(now + timedelta(days=30))))
    db.commit()

    res = client.get(f"/api/v1/analytics/projects/{proj.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # Phase 37 contract: list of {status, count}
    assert isinstance(data["status_distribution"], list)
    assert all({"status", "count"} <= set(d) for d in data["status_distribution"])
    # deadline buckets
    dl = data["deadlines"]
    assert dl["due_soon"] == 1 and dl["future"] == 1 and dl["overdue"] == 0
    assert data["total_tasks"] == 3


def test_dora_contract(client, db):
    headers = _register(client, "p38-dora@example.com")
    user = db.query(User).filter(User.email == "p38-dora@example.com").first()
    org = _make_org(db, user.id)
    h = {**headers, "X-Organization-Id": str(org.id)}

    # insufficient data path
    res = client.get("/api/v1/analytics/dora", headers=h)
    assert res.status_code == 200
    assert res.json()["deployment_frequency"] == "insufficient_data"

    # with data
    proj = Project(id=uuid4(), name="Dora proj", slug="p38-dora-proj",
                   organization_id=org.id, owner_id=user.id)
    db.add(proj)
    db.flush()
    base = datetime.now(timezone.utc) - timedelta(days=10)
    for i, status in enumerate([DeploymentStatus.FAILED, DeploymentStatus.SUCCESS]):
        db.add(Deployment(id=uuid4(), organization_id=org.id, project_id=proj.id,
                          status=status, created_at=base + timedelta(days=i)))
    db.commit()
    res = client.get("/api/v1/analytics/dora", headers=h)
    assert res.status_code == 200
    data = res.json()
    assert data["deployment_frequency"] != "insufficient_data"
    assert data["change_failure_rate"] == "50.0%"


def test_executive_and_dashboard_scoping(client, db):
    headers = _register(client, "p38-exec@example.com")
    user = db.query(User).filter(User.email == "p38-exec@example.com").first()
    org = _make_org(db, user.id)
    h = {**headers, "X-Organization-Id": str(org.id)}

    dash = client.get("/api/v1/analytics/dashboard", headers=h)
    assert dash.status_code == 200
    assert dash.json()["total_projects"] == 0

    db.add(Project(id=uuid4(), name="Exec proj", slug="p38-exec-proj",
                   organization_id=org.id, owner_id=user.id))
    db.commit()
    dash2 = client.get("/api/v1/analytics/dashboard", headers=h)
    assert dash2.json()["total_projects"] == 1

    exec_res = client.get("/api/v1/analytics/executive", headers=h)
    assert exec_res.status_code == 200
