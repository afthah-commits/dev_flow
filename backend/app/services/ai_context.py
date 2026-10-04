import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta

from app.models.project import Project
from app.models.task import Task
from app.models.sprint import Sprint
from app.models.github import ProjectGitHubRepository
from app.models.audit import AuditEvent
from app.models.delivery import Deployment, Release
from app.models.time import TimeEntry
from app.models.ai_project_memory import AIProjectMemory
from app.api.v1.github import get_gh_service

logger = logging.getLogger(__name__)

async def get_comprehensive_project_context(db: Session, project_id: UUID, user_id: UUID, org_id: UUID) -> Dict[str, Any]:
    """
    Build a comprehensive context dictionary for AI operations.
    Enforces RBAC by only querying data that belongs to the org/project.
    """
    context = {}

    # Verify project
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == org_id
    ).first()

    if not project:
        raise ValueError("Project not found or access denied")

    context["project"] = {
        "name": project.name,
        "status": project.status,
        "priority": project.priority,
        "tech_stack": project.tech_stack,
        "health_score": project.health_score,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "target_date": project.target_date.isoformat() if project.target_date else None,
    }

    # Tasks (limit 20 recent, get counts)
    total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
    done_tasks = db.query(Task).filter(Task.project_id == project_id, Task.status == 'DONE').count()
    in_progress = db.query(Task).filter(Task.project_id == project_id, Task.status == 'IN_PROGRESS').count()
    
    overdue_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status != 'DONE',
        Task.due_date < func.now()
    ).limit(10).all()

    blocked_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == 'BLOCKED'
    ).limit(10).all()

    context["tasks"] = {
        "total": total_tasks,
        "completed": done_tasks,
        "in_progress": in_progress,
        "overdue": [{"id": str(t.id), "key": t.key, "title": t.title} for t in overdue_tasks],
        "blocked": [{"id": str(t.id), "key": t.key, "title": t.title} for t in blocked_tasks]
    }

    # Sprints
    active_sprint = db.query(Sprint).filter(
        Sprint.project_id == project_id,
        Sprint.status == 'ACTIVE'
    ).first()

    if active_sprint:
        context["sprint"] = {
            "name": active_sprint.name,
            "goal": active_sprint.goal,
            "end_date": active_sprint.end_date.isoformat() if active_sprint.end_date else None
        }

    # Memory
    memories = db.query(AIProjectMemory).filter(
        AIProjectMemory.project_id == project_id
    ).all()
    context["memory"] = [{"category": m.category, "key": m.key, "value": m.value} for m in memories]

    # GitHub
    gh_repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if gh_repo:
        try:
            gh = get_gh_service(db, user_id)
            commits = await gh.get_commits(gh_repo.github_full_name, per_page=10)
            context["github"] = {
                "repository": gh_repo.github_full_name,
                "recent_commits": [{"message": c['commit']['message'], "author": c['commit']['author']['name']} for c in commits]
            }
        except Exception as e:
            logger.warning(f"Failed to fetch GitHub context: {e}")

    # Deployments
    recent_deployments = db.query(Deployment).filter(
        Deployment.project_id == project_id
    ).order_by(Deployment.created_at.desc()).limit(5).all()
    
    if recent_deployments:
        context["deployments"] = [
            {"id": str(d.id), "status": d.status, "environment_id": str(d.environment_id), "created_at": d.created_at.isoformat()}
            for d in recent_deployments
        ]

    # Time tracking
    recent_time = db.query(TimeEntry).filter(
        TimeEntry.project_id == project_id
    ).order_by(TimeEntry.start_time.desc()).limit(10).all()
    context["time_tracking"] = [
        {"duration_seconds": t.duration_seconds, "description": t.description}
        for t in recent_time
    ]

    return context
