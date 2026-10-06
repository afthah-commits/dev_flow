"""Phase 42 — GitHub analytics degraded-state contract.

Covers the optional `status` field on GET /analytics/projects/{id}/github:
- "ok" for live/cached GitHub data (incl. genuine zero activity)
- "unavailable" when GitHub-side fetch fails (degraded, zeros)
- "no_repository" when the project has no configured repo
- "not_connected" when the user has no GitHub integration
Plus org isolation, RBAC and no credential leakage. GitHub API fully mocked —
no real network requests.
"""
from unittest.mock import patch, AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.main import app
from app.api.v1 import analytics as analytics_module
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.project import Project
from app.models.github import GitHubConnection, ProjectGitHubRepository
from app.services.github_service import encrypt_token

URL = "/api/v1/analytics/projects/{pid}/github"


def _register(client, email):
    client.post("/api/v1/auth/register", json={"name": "P42", "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(autouse=True)
def _clear_gh_cache():
    analytics_module._GITHUB_COUNTS_CACHE.clear()
    yield
    analytics_module._GITHUB_COUNTS_CACHE.clear()


def _make_project(db, client, email, *, with_repo=True, with_connection=True):
    headers = _register(client, email)
    user = db.query(User).filter(User.email == email).first()
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=f"p42-{uuid4().hex[:8]}", created_by=user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id,
                              role=OrganizationRole.OWNER))
    project = Project(id=uuid4(), name=f"Proj {uuid4().hex[:6]}",
                      organization_id=org.id, slug=f"p42-proj-{uuid4().hex[:8]}",
                      owner_id=user.id)
    db.add(project)
    db.flush()
    if with_repo:
        db.add(ProjectGitHubRepository(
            id=uuid4(), project_id=project.id, github_repository_id="1",
            github_owner="octocat", github_name="hello-world",
            github_full_name="octocat/hello-world",
            github_url="https://github.com/octocat/hello-world"))
    if with_connection:
        db.add(GitHubConnection(id=uuid4(), user_id=user.id, github_user_id="1",
                                github_username="octocat",
                                access_token_encrypted=encrypt_token("ghs_testtoken")))
    db.commit()
    return headers, user, org, project


def _mock_gh(commits=None):
    gh = AsyncMock()
    gh.get_commits.return_value = commits if commits is not None else []
    gh.get_pull_requests.return_value = []
    gh.get_issues.return_value = []
    return gh


# ---------------------------------------------------------------------------
# Status values
# ---------------------------------------------------------------------------

def test_success_returns_status_ok(client, db):
    headers, user, org, project = _make_project(db, client, "p42-ok@example.com")
    gh = _mock_gh(commits=[{"sha": "a"}, {"sha": "b"}])
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["recent_commits"] == 2


def test_genuine_zero_activity_is_ok_not_degraded(client, db):
    """A connected, empty repo returns zeros with status 'ok' — real data."""
    headers, user, org, project = _make_project(db, client, "p42-zero@example.com")
    gh = _mock_gh(commits=[])
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    body = res.json()
    assert body["status"] == "ok"
    assert body["recent_commits"] == 0


def test_degraded_response_marks_unavailable(client, db):
    headers, user, org, project = _make_project(db, client, "p42-degraded@example.com")
    gh = AsyncMock()
    gh.get_commits.side_effect = HTTPException(status_code=502, detail="GitHub upstream error")
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "unavailable"
    assert body["recent_commits"] == 0
    # No GitHub error details leak through
    assert "upstream" not in res.text.lower()


def test_no_repository_marks_status(client, db):
    headers, user, org, project = _make_project(
        db, client, "p42-norepo@example.com", with_repo=False)
    res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "no_repository"


def test_not_connected_marks_status(client, db):
    """Repo configured but the user has no GitHub integration."""
    headers, user, org, project = _make_project(
        db, client, "p42-noconn@example.com", with_connection=False)
    res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "not_connected"


# ---------------------------------------------------------------------------
# Contract compatibility
# ---------------------------------------------------------------------------

def test_status_field_is_backward_compatible(client, db):
    """Numeric fields keep their names/types; status is additive."""
    headers, user, org, project = _make_project(db, client, "p42-compat@example.com")
    res = client.get(URL.format(pid=project.id), headers=headers)
    body = res.json()
    assert set(body.keys()) == {
        "recent_commits", "open_prs", "closed_prs", "open_issues",
        "closed_issues", "status",
    }
    for k in ("recent_commits", "open_prs", "closed_prs", "open_issues", "closed_issues"):
        assert isinstance(body[k], int)


# ---------------------------------------------------------------------------
# Security / isolation (unchanged guarantees)
# ---------------------------------------------------------------------------

def test_requires_authentication(client, db):
    res = client.get(URL.format(pid=uuid4()))
    assert res.status_code == 401


def test_non_member_cannot_read_project_github_analytics(client, db):
    _make_project(db, client, "p42-owner@example.com")
    outsider = _register(client, "p42-outsider@example.com")
    project = db.query(Project).first()
    res = client.get(URL.format(pid=project.id), headers=outsider)
    assert res.status_code in (403, 404)


def test_no_credentials_in_any_response(client, db):
    headers, user, org, project = _make_project(db, client, "p42-secrets@example.com")
    gh = AsyncMock()
    gh.get_commits.side_effect = HTTPException(status_code=401, detail="GitHub token expired or revoked")
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    assert "ghs_testtoken" not in res.text
    assert "token" not in res.text.lower()
    assert "access_token" not in res.json()
