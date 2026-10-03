from sqlalchemy.orm import Session
from uuid import UUID
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone

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

@router.get("/productivity")
def get_productivity_stats(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    team_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    from app.models.time import TimeEntry
    
    query = db.query(TimeEntry).filter(TimeEntry.organization_id == org_id)
    if date_from: query = query.filter(TimeEntry.started_at >= date_from)
    if date_to: query = query.filter(TimeEntry.started_at <= date_to)
    if project_id: query = query.filter(TimeEntry.project_id == project_id)
    if user_id: query = query.filter(TimeEntry.user_id == user_id)
    
    if team_id:
        from app.models.organization import TeamMember
        team_members = db.query(TeamMember.user_id).filter(TeamMember.team_id == team_id).all()
        team_user_ids = [tm[0] for tm in team_members]
        query = query.filter(TimeEntry.user_id.in_(team_user_ids))
        
    entries = query.all()
    
    total_seconds = sum(e.duration_seconds for e in entries)
    total_hours = total_seconds / 3600.0
    
    active_days = len(set(e.started_at.date() for e in entries))
    tasks_worked_on = len(set(e.task_id for e in entries if e.task_id))
    
    from app.models.task import Task, TaskStatus
    task_ids = list(set(e.task_id for e in entries if e.task_id))
    
    tasks_completed = 0
    estimated_hours = 0.0
    if task_ids:
        tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
        tasks_completed = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        estimated_hours = sum((t.estimate_hours or 0) for t in tasks)
        
    avg_hours_per_day = total_hours / active_days if active_days > 0 else 0
    avg_hours_per_task = total_hours / tasks_worked_on if tasks_worked_on > 0 else 0
    completion_rate = (tasks_completed / tasks_worked_on * 100) if tasks_worked_on > 0 else 0
    
    return {
        "total_hours": total_hours,
        "active_days": active_days,
        "tasks_completed": tasks_completed,
        "tasks_worked_on": tasks_worked_on,
        "avg_hours_per_day": avg_hours_per_day,
        "avg_hours_per_task": avg_hours_per_task,
        "estimated_hours": estimated_hours,
        "completion_rate": completion_rate
    }


@router.get("/team-workload")
def get_team_workload(
    team_id: Optional[UUID] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    
    from app.models.organization import OrganizationMember, TeamMember
    from app.models.user import User
    from app.models.time import TimeEntry
    from app.models.task import Task, TaskStatus
    
    user_query = db.query(User).join(OrganizationMember, OrganizationMember.user_id == User.id).filter(OrganizationMember.organization_id == org_id)
    
    if team_id:
        user_query = user_query.join(TeamMember, TeamMember.user_id == User.id).filter(TeamMember.team_id == team_id)
        
    users = user_query.all()
    user_ids = [u.id for u in users]
    
    entries = db.query(TimeEntry).filter(TimeEntry.organization_id == org_id, TimeEntry.user_id.in_(user_ids)).all()
    tasks = db.query(Task).filter(Task.assignee_id.in_(user_ids)).all()
    
    workload = []
    
    for u in users:
        u_entries = [e for e in entries if e.user_id == u.id]
        u_tasks = [t for t in tasks if t.assignee_id == u.id]
        
        tracked = sum(e.duration_seconds for e in u_entries) / 3600.0
        assigned = len(u_tasks)
        completed = len([t for t in u_tasks if t.status == TaskStatus.DONE])
        
        now = datetime.now(timezone.utc)
        overdue = len([t for t in u_tasks if t.due_date and t.due_date < now and t.status != TaskStatus.DONE])
        
        estimated = sum((t.estimate_hours or 0) for t in u_tasks)
        
        # Calculate a simple workload percentage based on a 40 hour week
        # Just an example approximation
        percentage = min(100.0, (tracked / 40.0) * 100) if tracked > 0 else 0
        
        workload.append({
            "user_id": u.id,
            "user_name": u.name,
            "tracked_hours": tracked,
            "assigned_tasks": assigned,
            "completed_tasks": completed,
            "overdue_tasks": overdue,
            "estimated_hours": estimated,
            "workload_percentage": percentage
        })
        
    return workload

