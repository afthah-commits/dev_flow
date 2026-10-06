"""Phase 39 — Analytics client contract & UX completion.

Covers the two endpoints added so frontend API clients reference real routes:
- GET /api/v1/analytics/team-workload  (consumed by ProductivityAnalytics page)
- GET /api/v1/analytics/projects/{id}/github  (consumed by ProjectAnalytics panel)

Security: auth (401), org membership (403), RBAC permission, tenant isolation.
Contract: response shape matches the frontend types (TeamWorkloadItem,
GitHubAnalyticsResponse) and empty states are safe.
"""
from uuid import uuid4

from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole, Team, TeamMember
from app.models.project import Project
from app.models.task import Task, TaskStatus


def _register(client, email, name="P39 User"):
    client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _make_user(db, uid, email=None):
    if db.query(User).filter(User.id == uid).first():
        return
    from app.core.security import get_password_hash
    db.add(User(id=uid, name="P39", email=email or f"{uid.hex[:12]}@p39.example.com",
                password_hash=get_password_hash("password123")))
    db.commit()


def _make_org(db, owner_id, slug=None):
    _make_user(db, owner_id)
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=slug or f"p39-{uuid4().hex[:8]}", created_by=owner_id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=owner_id,
                              role=OrganizationRole.OWNER))
    db.commit()
    return org


def _make_team(db, org, user_id):
    team = Team(id=uuid4(), organization_id=org.id, name=f"Team {uuid4().hex[:6]}",
                slug=f"p39-team-{uuid4().hex[:8]}", created_by=org.created_by)
    db.add(team)
    db.flush()
    db.add(TeamMember(id=uuid4(), team_id=team.id, user_id=user_id))
    db.commit()
    return team


def _make_project(db, org, owner_id):
    project = Project(id=uuid4(), name=f"Proj {uuid4().hex[:6]}", organization_id=org.id,
                      slug=f"p39-proj-{uuid4().hex[:8]}", owner_id=owner_id)
    db.add(project)
    db.commit()
    return project


# ---------------------------------------------------------------------------
# GET /analytics/team-workload
# ---------------------------------------------------------------------------

def test_team_workload_auth_required(client, db):
    res = client.get("/api/v1/analytics/team-workload",
                     headers={"X-Organization-Id": str(uuid4())})
    assert res.status_code == 401


def test_team_workload_rejects_non_member(client, db):
    owner_id, outsider_id = uuid4(), uuid4()
    org = _make_org(db, owner_id)
    headers = _register(client, f"out-{outsider_id.hex[:8]}@p39.example.com")
    res = client.get("/api/v1/analytics/team-workload",
                     headers={**headers, "X-Organization-Id": str(org.id)})
    assert res.status_code == 403


def test_team_workload_seeded_member_contract(client, db):
    owner_id = uuid4()
    headers = _register(client, "p39-workload@example.com")
    owner_id = db.query(User).filter(User.email == "p39-workload@example.com").first().id
    org = _make_org(db, owner_id)
    _make_team(db, org, owner_id)
    project = _make_project(db, org, owner_id)
    db.add(Task(id=uuid4(), project_id=project.id, title="W1", status=TaskStatus.TODO,
                assignee_id=owner_id, creator_id=owner_id, estimate_hours=4.0))
    db.add(Task(id=uuid4(), project_id=project.id, title="W2", status=TaskStatus.DONE,
                assignee_id=owner_id, creator_id=owner_id))
    db.commit()

    res = client.get("/api/v1/analytics/team-workload",
                     headers={**headers, "X-Organization-Id": str(org.id)})
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list) and len(items) == 1
    item = items[0]
    # Contract pinned to the frontend TeamWorkload type
    assert set(item) == {"user_id", "user_name", "tracked_hours", "assigned_tasks",
                         "completed_tasks", "overdue_tasks", "estimated_hours",
                         "workload_percentage"}
    assert item["assigned_tasks"] == 2
    assert item["completed_tasks"] == 1
    assert item["estimated_hours"] == 4.0
    assert item["overdue_tasks"] == 0


def test_team_workload_tenant_isolation(client, db):
    a_id, b_id = uuid4(), uuid4()
    _register(client, "p39-iso-a@example.com")
    headers_b = _register(client, "p39-iso-b@example.com")
    a_id = db.query(User).filter(User.email == "p39-iso-a@example.com").first().id
    b_id = db.query(User).filter(User.email == "p39-iso-b@example.com").first().id
    org_a, org_b = _make_org(db, a_id), _make_org(db, b_id)
    _make_team(db, org_a, a_id)
    project = _make_project(db, org_a, a_id)
    db.add(Task(id=uuid4(), project_id=project.id, title="A-task", status=TaskStatus.TODO,
                assignee_id=a_id, creator_id=a_id))
    db.commit()

    res = client.get("/api/v1/analytics/team-workload",
                     headers={**headers_b, "X-Organization-Id": str(org_b.id)})
    assert res.status_code == 200
    # Org B has a team but no members seeded -> no org A data leaks
    assert all(i["user_id"] != str(a_id) for i in res.json())


def test_team_workload_empty_team_returns_empty_list(client, db):
    headers = _register(client, "p39-empty@example.com")
    owner_id = db.query(User).filter(User.email == "p39-empty@example.com").first().id
    org = _make_org(db, owner_id)  # no teams
    res = client.get("/api/v1/analytics/team-workload",
                     headers={**headers, "X-Organization-Id": str(org.id)})
    assert res.status_code == 200
    assert res.json() == []


# ---------------------------------------------------------------------------
# GET /analytics/projects/{id}/github
# ---------------------------------------------------------------------------

def test_project_github_auth_required(client, db):
    res = client.get(f"/api/v1/analytics/projects/{uuid4()}/github")
    assert res.status_code == 401


def test_project_github_unknown_project_404(client, db):
    headers = _register(client, "p39-gh-404@example.com")
    owner_id = db.query(User).filter(User.email == "p39-gh-404@example.com").first().id
    org = _make_org(db, owner_id)
    res = client.get(f"/api/v1/analytics/projects/{uuid4()}/github", headers=headers)
    assert res.status_code == 404


def test_project_github_rejects_foreign_org_member(client, db):
    a_id, b_id = uuid4(), uuid4()
    headers_a = _register(client, "p39-gh-a@example.com")
    headers_b = _register(client, "p39-gh-b@example.com")  # member of no org
    a_id = db.query(User).filter(User.email == "p39-gh-a@example.com").first().id
    org_a = _make_org(db, a_id)
    project = _make_project(db, org_a, a_id)
    res = client.get(f"/api/v1/analytics/projects/{project.id}/github", headers=headers_b)
    assert res.status_code in (403, 404)


def test_project_github_no_repo_returns_zeros(client, db):
    headers = _register(client, "p39-gh-zero@example.com")
    owner_id = db.query(User).filter(User.email == "p39-gh-zero@example.com").first().id
    org = _make_org(db, owner_id)
    project = _make_project(db, org, owner_id)
    res = client.get(f"/api/v1/analytics/projects/{project.id}/github", headers=headers)
    assert res.status_code == 200
    # Contract pinned to the frontend GitHubAnalyticsResponse type
    assert res.json() == {"recent_commits": 0, "open_prs": 0, "closed_prs": 0,
                          "open_issues": 0, "closed_issues": 0}


def test_project_github_route_registered_once():
    from app.main import app
    from collections import Counter
    matches = [(r.path, tuple(sorted(r.methods)))
               for r in app.routes
               if getattr(r, "path", "") == "/api/v1/analytics/projects/{project_id}/github"]
    assert len(matches) == 1, f"expected exactly one route, got {matches}"
