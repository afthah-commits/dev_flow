
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.schemas.analytics import (
    DashboardOverview, ProjectAnalyticsResponse,
    ExecutiveAnalyticsResponse, TeamAnalyticsResponse, SprintAnalyticsResponse,
    TimeAnalyticsResponse, WorkflowAnalyticsResponse,
    AutomationAnalyticsResponse, ClientAnalyticsResponse, KnowledgeAnalyticsResponse,
    CollaborationAnalyticsResponse, UsageAnalyticsResponse,
    AnalyticsQueryRequest, AnalyticsQueryResponse
)
from app.services.analytics_service import (
    get_dashboard_overview, get_project_analytics, get_executive_analytics,
    get_team_analytics, get_sprint_analytics,
    get_time_analytics, get_workflow_analytics, get_automation_analytics,
    get_client_analytics, get_knowledge_analytics, get_collaboration_analytics,
    get_usage_analytics, execute_analytics_query, get_delivery_metrics, get_dora_metrics,
    get_team_workload
)
from app.api.v1.reports import check_permission
# TeamWorkloadItem is defined in schemas/time.py (it belongs to the time domain)
from app.schemas.time import TeamWorkloadItem
from app.schemas.analytics import GitHubAnalyticsResponse
from app.models.github import GitHubConnection, ProjectGitHubRepository
from app.services.github_service import GitHubService, decrypt_token

router = APIRouter()

# ---------------------------------------------------------------------------
# GitHub analytics counts — reliability helpers
#
# Caching: lightweight in-process TTL cache of *aggregate counts only* (no
# tokens/credentials). Deliberately not Redis/Celery — the panel tolerates
# slightly stale counts, and a process restart simply repopulates.
# ---------------------------------------------------------------------------

_GITHUB_COUNTS_CACHE: dict = {}  # key -> (expires_at_utc, GitHubAnalyticsResponse)
GITHUB_COUNTS_TTL_SECONDS = 300


def _cached_github_counts(key: str):
    entry = _GITHUB_COUNTS_CACHE.get(key)
    if entry and entry[0] > datetime.now(timezone.utc):
        return entry[1]
    return None


def _store_github_counts(key: str, response) -> None:
    # Cap the cache so a flood of project ids cannot grow it unbounded.
    if len(_GITHUB_COUNTS_CACHE) >= 256:
        now = datetime.now(timezone.utc)
        for k in [k for k, (exp, _) in _GITHUB_COUNTS_CACHE.items() if exp <= now]:
            _GITHUB_COUNTS_CACHE.pop(k, None)
        if len(_GITHUB_COUNTS_CACHE) >= 256:
            _GITHUB_COUNTS_CACHE.clear()
    _GITHUB_COUNTS_CACHE[key] = (
        datetime.now(timezone.utc) + timedelta(seconds=GITHUB_COUNTS_TTL_SECONDS),
        response,
    )


def _github_counts_response(status: str) -> GitHubAnalyticsResponse:
    """Safe zero-count value with a status marker (Phase 42) so the panel can
    distinguish: 'ok' = live/cached data, 'not_connected' = user has no GitHub
    integration, 'no_repository' = project has no repo configured,
    'unavailable' = GitHub-side failure (degraded). No error details, tokens,
    or credentials are ever exposed."""
    return GitHubAnalyticsResponse(
        recent_commits=0, open_prs=0, closed_prs=0, open_issues=0, closed_issues=0,
        status=status)

@router.get("/dashboard", response_model=DashboardOverview)
def get_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_dashboard_overview(db, org_id)

@router.get("/executive", response_model=ExecutiveAnalyticsResponse)
def get_executive_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.executive")
    return get_executive_analytics(db, org_id, date_from, date_to)

@router.get("/projects/{project_id}", response_model=ProjectAnalyticsResponse)
def get_project_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: UUID
) -> Any:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    member = deps.require_organization_member(db, current_user.id, project.organization_id)
    check_permission(db, member, "analytics.projects")
    return get_project_analytics(db, project_id)

@router.get("/projects/{project_id}/github", response_model=GitHubAnalyticsResponse)
async def get_project_github_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: UUID
) -> Any:
    """Counts backing the ProjectAnalytics 'GitHub Activity' panel.

    Reuses the GitHub service the rest of the integration uses; a project
    without a connected repo returns zeros rather than an error so the panel
    can render its 'connect GitHub' fallback.

    Reliability: any GitHub-side failure (unauthorized/revoked token, rate
    limit, 5xx, timeout, malformed payload) degrades to a zero-count response
    instead of surfacing GitHub errors to this endpoint's caller. Aggregate
    counts are cached in-process for a short TTL; only counts are cached,
    never credentials.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    member = deps.require_organization_member(db, current_user.id, project.organization_id)
    check_permission(db, member, "analytics.projects")

    repo = db.query(ProjectGitHubRepository).filter(
        ProjectGitHubRepository.project_id == project_id).first()
    if not repo:
        return _github_counts_response("no_repository")

    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if not conn:
        return _github_counts_response("not_connected")

    cache_key = f"gh-counts:{project_id}:{repo.github_full_name}"
    cached = _cached_github_counts(cache_key)
    if cached is not None:
        return cached

    counts = _github_counts_response("unavailable")
    try:
        gh = GitHubService(decrypt_token(conn.access_token_encrypted))
        commits = await gh.get_commits(repo.github_full_name, per_page=30)
        pulls = await gh.get_pull_requests(repo.github_full_name, state="all", per_page=100)
        issues = await gh.get_issues(repo.github_full_name, state="all", per_page=100)
        counts = GitHubAnalyticsResponse(
            recent_commits=len(commits),
            open_prs=sum(1 for p in pulls if p.get("state") == "open"),
            closed_prs=sum(1 for p in pulls if p.get("state") == "closed"),
            open_issues=sum(1 for i in issues if i.get("state") == "open"),
            closed_issues=sum(1 for i in issues if i.get("state") == "closed"),
            status="ok",
        )
        # Only successful fetches are cached — a failure stays uncached so the
        # next request retries GitHub instead of pinning zeros for the TTL.
        _store_github_counts(cache_key, counts)
    except HTTPException:
        # GitHub service raises HTTPException for auth/rate-limit/404; degrade
        # to zeros rather than leaking a GitHub-side error to this caller.
        pass
    except Exception:
        # Network/timeout/malformed JSON or any unexpected shape: safe zeros.
        pass

    return counts

@router.get("/teams/{team_id}", response_model=TeamAnalyticsResponse)
def get_team_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    team_id: UUID,
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.teams")
    return get_team_analytics(db, team_id, org_id)

@router.get("/sprints/{sprint_id}", response_model=SprintAnalyticsResponse)
def get_sprint_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    sprint_id: UUID,
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.projects")
    return get_sprint_analytics(db, sprint_id, org_id)

@router.get("/delivery")
def get_delivery_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
    project_id: Optional[UUID] = None,
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_delivery_metrics(db, org_id, project_id)

@router.get("/dora")
def get_dora_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
    project_id: Optional[UUID] = None,
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_dora_metrics(db, org_id, project_id)

@router.get("/productivity", response_model=TimeAnalyticsResponse)
def get_time_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_time_analytics(db, org_id)

@router.get("/team-workload", response_model=List[TeamWorkloadItem])
def get_team_workload_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_team_workload(db, org_id)

@router.get("/workflow", response_model=WorkflowAnalyticsResponse)
def get_workflow_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_workflow_analytics(db, org_id)

@router.get("/automation", response_model=AutomationAnalyticsResponse)
def get_automation_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_automation_analytics(db, org_id)

@router.get("/clients", response_model=ClientAnalyticsResponse)
def get_client_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_client_analytics(db, org_id)

@router.get("/knowledge", response_model=KnowledgeAnalyticsResponse)
def get_knowledge_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_knowledge_analytics(db, org_id)

@router.get("/collaboration", response_model=CollaborationAnalyticsResponse)
def get_collaboration_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_collaboration_analytics(db, org_id)

@router.get("/usage", response_model=UsageAnalyticsResponse)
def get_usage_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_usage_analytics(db, org_id)

@router.post("/query", response_model=AnalyticsQueryResponse)
def query_analytics_api(
    *,
    request: AnalyticsQueryRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    
    ALLOWED_METRICS = [
        "tasks.completed", "tasks.overdue", "sprint.velocity",
        "time.tracked_hours", "deployments.success_rate",
        "releases.count", "workflows.success_rate",
        "projects.count"
    ]
    
    if request.metric not in ALLOWED_METRICS:
        raise HTTPException(status_code=400, detail="Unknown metric")
        
    return execute_analytics_query(db, org_id, request)


@router.post("/export")
def export_analytics_data(
    *,
    request: AnalyticsQueryRequest,
    format: str = Query("csv"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.export")
    
    # Reuse query executor
    result = execute_analytics_query(db, org_id, request)
    
    # Note: the real DevFlow export engine uses StreamingResponse, 
    # but here we follow Phase 18 Report export which returns JSON payload with format
    return {"data": result.data, "format": format}
