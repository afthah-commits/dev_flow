from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Any

from app.api import deps
from app.models.user import User
from app.schemas.analytics import DashboardOverview, ProjectAnalyticsResponse, GitHubAnalyticsResponse
from app.services.analytics_service import get_dashboard_overview, get_project_analytics
from app.api.v1.github import get_project_auth, get_gh_service
from app.models.github import ProjectGitHubRepository

router = APIRouter()

@router.get("/dashboard", response_model=DashboardOverview)
def get_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)
    return get_dashboard_overview(db, org_id)

@router.get("/projects/{project_id}", response_model=ProjectAnalyticsResponse)
def get_project_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: UUID
) -> Any:
    from app.models.project import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)
    return get_project_analytics(db, project_id)

@router.get("/projects/{project_id}/github", response_model=GitHubAnalyticsResponse)
async def get_project_github_analytics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: UUID
) -> Any:
    from app.models.project import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)
    repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="GitHub not connected")
        
    gh = get_gh_service(db, current_user.id)
    
    # Bounded queries
    commits = await gh.get_commits(repo.github_full_name, per_page=10)
    prs = await gh.get_pull_requests(repo.github_full_name, state="all", per_page=10)
    issues = await gh.get_issues(repo.github_full_name, state="all", per_page=10)
    
    return {
        "recent_commits": len(commits),
        "open_prs": sum(1 for p in prs if p["state"] == "open"),
        "closed_prs": sum(1 for p in prs if p["state"] == "closed"),
        "open_issues": sum(1 for i in issues if i["state"] == "open"),
        "closed_issues": sum(1 for i in issues if i["state"] == "closed")
    }
