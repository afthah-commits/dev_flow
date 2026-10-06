"""Phase 40 — GitHub analytics reliability & analytics client contract hardening.

Connected-path coverage for GET /analytics/projects/{id}/github with the
external GitHub API fully mocked — no real network requests are made.

Failure semantics: any GitHub-side failure (revoked token, rate limit, 5xx,
timeout, malformed payload) degrades to a zero-count 200 so the ProjectAnalytics
panel renders its fallback. Aggregate counts are cached in-process (TTL), and
no credentials ever appear in the response.
"""
from unittest.mock import patch, AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import TimeoutException

from app.main import app
from app.api.v1 import analytics as analytics_module
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.project import Project
from app.models.github import GitHubConnection, ProjectGitHubRepository
from app.services.github_service import encrypt_token

ZERO = {"recent_commits": 0, "open_prs": 0, "closed_prs": 0,
        "open_issues": 0, "closed_issues": 0, "status": "unavailable"}
OK_ZERO = {"recent_commits": 0, "open_prs": 0, "closed_prs": 0,
           "open_issues": 0, "closed_issues": 0, "status": "ok"}


def _register(client, email):
    client.post("/api/v1/auth/register", json={"name": "P40", "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(autouse=True)
def _clear_gh_cache():
    analytics_module._GITHUB_COUNTS_CACHE.clear()
    yield
    analytics_module._GITHUB_COUNTS_CACHE.clear()


def _make_connected(db, client, email):
    headers = _register(client, email)
    user = db.query(User).filter(User.email == email).first()
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=f"p40-{uuid4().hex[:8]}", created_by=user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id,
                              role=OrganizationRole.OWNER))
    project = Project(id=uuid4(), name=f"Proj {uuid4().hex[:6]}",
                      organization_id=org.id, slug=f"p40-proj-{uuid4().hex[:8]}",
                      owner_id=user.id)
    db.add(project)
    db.flush()
    db.add(ProjectGitHubRepository(id=uuid4(), project_id=project.id,
                                   github_repository_id="1",
                                   github_owner="octocat", github_name="hello-world",
                                   github_full_name="octocat/hello-world",
                                   github_url="https://github.com/octocat/hello-world"))
    db.add(GitHubConnection(id=uuid4(), user_id=user.id, github_user_id="1",
                            github_username="octocat",
                            access_token_encrypted=encrypt_token("ghs_testtoken")))
    db.commit()
    return headers, user, org, project


def _mock_gh(commits=None, pulls=None, issues=None):
    gh = AsyncMock()
    gh.get_commits.return_value = commits if commits is not None else []
    gh.get_pull_requests.return_value = pulls if pulls is not None else []
    gh.get_issues.return_value = issues if issues is not None else []
    return gh


URL = "/api/v1/analytics/projects/{pid}/github"


# ---------------------------------------------------------------------------
# Connected success path (mocked)
# ---------------------------------------------------------------------------

def test_connected_project_returns_real_counts(client, db):
    headers, user, org, project = _make_connected(
        db, client, "p40-connected@example.com")
    gh = _mock_gh(
        commits=[{"sha": "a"}, {"sha": "b"}, {"sha": "c"}],
        pulls=[{"state": "open"}, {"state": "closed"}, {"state": "open"}],
        issues=[{"state": "open"}, {"state": "closed"}],
    )
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    assert res.json() == {"recent_commits": 3, "open_prs": 2, "closed_prs": 1,
                          "open_issues": 1, "closed_issues": 1, "status": "ok"}
    # No credentials anywhere in the response
    assert "ghs_testtoken" not in res.text
    assert "access_token" not in res.json()


def test_response_is_cached_within_ttl(client, db):
    headers, user, org, project = _make_connected(
        db, client, "p40-cache@example.com")
    gh = _mock_gh(commits=[{"sha": "a"}])
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        r1 = client.get(URL.format(pid=project.id), headers=headers)
        r2 = client.get(URL.format(pid=project.id), headers=headers)
    assert r1.status_code == r2.status_code == 200
    # Second call must be served from cache: service invoked once
    assert gh.get_commits.await_count == 1


def test_cache_expires_after_ttl(client, db):
    headers, user, org, project = _make_connected(
        db, client, "p40-ttl@example.com")
    gh = _mock_gh(commits=[{"sha": "a"}])
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh), \
         patch.object(analytics_module, "GITHUB_COUNTS_TTL_SECONDS", -1):
        r1 = client.get(URL.format(pid=project.id), headers=headers)
        r2 = client.get(URL.format(pid=project.id), headers=headers)
    assert r1.status_code == r2.status_code == 200
    assert gh.get_commits.await_count == 2  # re-fetched after expiry


# ---------------------------------------------------------------------------
# Failure semantics — every GitHub-side failure degrades to zeros (200)
# ---------------------------------------------------------------------------

def test_github_token_revoked_degrades_to_zeros(client, db):
    headers, user, org, project = _make_connected(
        db, client, "p40-revoked@example.com")
    gh = AsyncMock()
    gh.get_commits.side_effect = HTTPException(status_code=401,
                                               detail="GitHub token expired or revoked")
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    assert res.json() == ZERO
    assert "token" not in res.text.lower()


def test_github_rate_limit_degrades_to_zeros(client, db):
    headers, user, org, project = _make_connected(
        db, client, "p40-ratelimit@example.com")
    gh = AsyncMock()
    gh.get_commits.side_effect = HTTPException(status_code=403,
                                               detail="GitHub API rate limit exceeded")
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    assert res.json() == ZERO


def test_github_server_error_degrades_to_zeros(client, db):
    headers, user, org, project = _make_connected(
        db, client, "p40-5xx@example.com")
    gh = AsyncMock()
    gh.get_pull_requests.side_effect = HTTPException(status_code=502,
                                                     detail="GitHub upstream error")
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    assert res.json() == ZERO


def test_github_timeout_degrades_to_zeros(client, db):
    headers, user, org, project = _make_connected(
        db, client, "p40-timeout@example.com")
    gh = AsyncMock()
    gh.get_commits.side_effect = TimeoutException("timed out")
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    assert res.json() == ZERO


def test_github_malformed_response_degrades_to_zeros(client, db):
    headers, user, org, project = _make_connected(
        db, client, "p40-malformed@example.com")
    gh = _mock_gh(pulls="not-a-list")  # string instead of list -> .get() fails
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    assert res.json() == ZERO


def test_failed_counts_are_not_cached(client, db):
    """A failure should not pin zeros for the TTL — next call retries."""
    headers, user, org, project = _make_connected(
        db, client, "p40-retry@example.com")
    gh = AsyncMock()
    gh.get_commits.side_effect = [HTTPException(status_code=403, detail="rate limit"),
                                  [{"sha": "a"}]]
    gh.get_pull_requests.return_value = []
    gh.get_issues.return_value = []
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        r1 = client.get(URL.format(pid=project.id), headers=headers)
        r2 = client.get(URL.format(pid=project.id), headers=headers)
    assert r1.json() == ZERO
    assert r2.json() == {"recent_commits": 1, "open_prs": 0, "closed_prs": 0,
                         "open_issues": 0, "closed_issues": 0, "status": "ok"}


# ---------------------------------------------------------------------------
# Not-connected / repo-missing paths (cache never engaged)
# ---------------------------------------------------------------------------

def test_repo_missing_degrades_to_zeros_without_touching_github(client, db):
    headers, user, org, project = _make_connected(
        db, client, "p40-norepo@example.com")
    # Remove the repo link
    db.query(ProjectGitHubRepository).delete()
    db.commit()
    gh = _mock_gh()
    with patch.object(analytics_module.GitHubService, "__new__", return_value=gh):
        res = client.get(URL.format(pid=project.id), headers=headers)
    assert res.status_code == 200
    # Phase 42: repo-missing is now distinguishable from a GitHub failure.
    assert res.json() == {**ZERO, "status": "no_repository"}
    assert gh.get_commits.await_count == 0


# ---------------------------------------------------------------------------
# Security — permission model unchanged
# ---------------------------------------------------------------------------

def test_connected_project_requires_auth(client, db):
    res = client.get(URL.format(pid=uuid4()))
    assert res.status_code == 401


def test_connected_project_foreign_org_member_rejected(client, db):
    _make_connected(db, client, "p40-owner@example.com")
    headers_b = _register(client, "p40-outsider@example.com")  # member of no org
    project = db.query(Project).first()
    res = client.get(URL.format(pid=project.id), headers=headers_b)
    assert res.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Workload semantics — pinned edge cases (service level)
# ---------------------------------------------------------------------------

def _seed_workload(db, email, *, estimate_hours, tracked_seconds, completed=False,
                   overdue=False, team=True):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        headers = None
        user = User(id=uuid4(), name="P40", email=email,
                    password_hash="x" * 64)
        db.add(user)
        db.flush()
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=f"p40-wl-{uuid4().hex[:8]}", created_by=user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id,
                              role=OrganizationRole.OWNER))
    from app.models.organization import Team, TeamMember
    if team:
        db.add(Team(id=uuid4(), organization_id=org.id, name="T",
                    slug=f"p40-t-{uuid4().hex[:8]}", created_by=user.id))
        db.flush()
        db.add(TeamMember(id=uuid4(), team_id=db.query(Team).order_by(Team.id.desc()).first().id,
                          user_id=user.id))
    project = Project(id=uuid4(), name="P", organization_id=org.id,
                      slug=f"p40-p-{uuid4().hex[:8]}", owner_id=user.id)
    db.add(project)
    db.flush()
    from datetime import datetime, timedelta, timezone
    from app.models.task import Task, TaskStatus
    from app.models.time import TimeEntry
    task = Task(id=uuid4(), project_id=project.id, title="t",
                status=TaskStatus.DONE if completed else TaskStatus.TODO,
                assignee_id=user.id, creator_id=user.id,
                estimate_hours=estimate_hours,
                due_date=(datetime.now(timezone.utc) - timedelta(days=1))
                if overdue else None)
    db.add(task)
    db.commit()
    if tracked_seconds:
        db.add(TimeEntry(id=uuid4(), organization_id=org.id, user_id=user.id,
                         project_id=project.id, task_id=task.id,
                         duration_seconds=tracked_seconds,
                         started_at=datetime.now(timezone.utc) - timedelta(hours=1),
                         ended_at=datetime.now(timezone.utc)))
        db.commit()
    return org, user


def test_workload_zero_estimates_zero_tracking(client, db):
    org, user = _seed_workload(db, "p40-wl-zero@example.com",
                               estimate_hours=0.0, tracked_seconds=0)
    from app.services.analytics_service import get_team_workload
    items = get_team_workload(db, org.id)
    assert len(items) == 1
    assert items[0]["estimated_hours"] == 0.0
    assert items[0]["tracked_hours"] == 0.0
    assert items[0]["workload_percentage"] == 0.0  # no division blowup


def test_workload_exact_capacity_is_100(client, db):
    # 4h estimated, 4h tracked (14400s) -> exactly 100%
    org, user = _seed_workload(db, "p40-wl-100@example.com",
                               estimate_hours=4.0, tracked_seconds=14400)
    from app.services.analytics_service import get_team_workload
    items = get_team_workload(db, org.id)
    assert items[0]["workload_percentage"] == pytest.approx(100.0)


def test_workload_over_capacity_exceeds_100(client, db):
    # 2h estimated, 8h tracked -> 400% (frontend renders red > 100)
    org, user = _seed_workload(db, "p40-wl-over@example.com",
                               estimate_hours=2.0, tracked_seconds=28800)
    from app.services.analytics_service import get_team_workload
    items = get_team_workload(db, org.id)
    assert items[0]["workload_percentage"] == pytest.approx(400.0)


def test_workload_tracked_without_estimates_is_zero(client, db):
    # Tracking exists but no estimates -> 0, not a blowup
    org, user = _seed_workload(db, "p40-wl-noest@example.com",
                               estimate_hours=0.0, tracked_seconds=7200)
    from app.services.analytics_service import get_team_workload
    items = get_team_workload(db, org.id)
    assert items[0]["workload_percentage"] == 0.0
    assert items[0]["tracked_hours"] == pytest.approx(2.0)


def test_workload_no_team_membership_yields_empty(client, db):
    org, user = _seed_workload(db, "p40-wl-noteam@example.com",
                               estimate_hours=4.0, tracked_seconds=3600,
                               team=False)
    from app.services.analytics_service import get_team_workload
    assert get_team_workload(db, org.id) == []


# ---------------------------------------------------------------------------
# Analytics client contract validation (static, no network)
# ---------------------------------------------------------------------------

def _pattern_for(backend_path: str) -> str:
    """FastAPI path -> regex: /api/v1 prefix stripped, {param} -> [^/]+ segment."""
    import re as _re
    tail = _re.escape(backend_path[len("/api/v1"):])
    # _re.escape leaves \{name\}; turn those into a single-segment wildcard
    return _re.sub(r"\\\{[^}]+\\\}", "[^/]+", tail)


def _frontend_api_urls():
    """Extract api.get/post/patch/delete URLs from frontend API clients."""
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    urls = set()
    pattern = re.compile(r"""api\.(?:get|post|patch|delete|put)\(\s*[\`'\"]([^\\`'\"]+)""")
    for f in root.rglob("*.ts"):
        urls |= set(pattern.findall(f.read_text(encoding="utf-8", errors="ignore")))
    for f in root.rglob("*.tsx"):
        urls |= set(pattern.findall(f.read_text(encoding="utf-8", errors="ignore")))
    return urls


def test_frontend_analytics_time_urls_exist_in_backend():
    from collections import Counter
    backend = [(getattr(r, "path", ""), tuple(sorted(getattr(r, "methods", []) or [])))
               for r in app.routes if hasattr(r, "methods")]
    assert not [p for p, c in Counter(backend).items() if c > 1], \
        "duplicate backend routes detected"
    paths = {p for p, _ in backend}
    checked = 0
    for raw in _frontend_api_urls():
        if not (raw.startswith("/analytics") or raw.startswith("/time")):
            continue
        checked += 1
        normalized = raw
        # template-literal interpolation -> single path segment placeholder
        import re as _re
        normalized = _re.sub(r"\$\{[^}]*\}", "PARAM", normalized)
        matched = any(
            p.startswith("/api/v1") and
            _re.fullmatch(_pattern_for(p), normalized)
            for p in paths
        )
        assert matched, f"frontend references nonexistent backend route: {raw}"
    # sanity: the scan actually found the analytics clients
    assert checked >= 10, f"contract scan checked only {checked} URLs"


def test_github_analytics_route_registered_exactly_once():
    from collections import Counter
    matches = [(r.path, tuple(sorted(r.methods)))
               for r in app.routes
               if getattr(r, "path", "") == "/api/v1/analytics/projects/{project_id}/github"]
    assert len(matches) == 1
