import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.models.project import Project
from app.models.task import Task
from app.models.sprint import Sprint
from app.models.delivery import Deployment
from app.models.organization import OrganizationMember

from app.schemas.ai import (
    ProjectForecast, ForecastAssumptions, ProjectRiskEngineResult, RiskItem,
    SprintCapacityRecommendation, TaskPriorityScore
)

logger = logging.getLogger(__name__)

def calculate_project_forecast(db: Session, project_id: UUID, org_id: UUID) -> ProjectForecast:
    now = datetime.now(timezone.utc)
    
    # 1. Total and remaining tasks
    total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
    completed_tasks = db.query(Task).filter(Task.project_id == project_id, Task.status == 'DONE').count()
    remaining_tasks = total_tasks - completed_tasks
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
    
    # 2. Velocity (tasks completed in last 14 days)
    two_weeks_ago = now - timedelta(days=14)
    tasks_done_last_14 = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == 'DONE',
        Task.updated_at >= two_weeks_ago
    ).count()
    
    velocity_tasks_per_week = tasks_done_last_14 / 2.0
    if velocity_tasks_per_week == 0:
        velocity_tasks_per_week = 0.5 # assume very slow progress to avoid div by zero
        
    weeks_remaining = remaining_tasks / velocity_tasks_per_week
    estimated_completion_date = now + timedelta(days=weeks_remaining * 7)
    
    # Story points
    remaining_points = db.query(func.sum(Task.estimate_points)).filter(
        Task.project_id == project_id,
        Task.status != 'DONE'
    ).scalar() or 0
    
    points_done_last_14 = db.query(func.sum(Task.estimate_points)).filter(
        Task.project_id == project_id,
        Task.status == 'DONE',
        Task.updated_at >= two_weeks_ago
    ).scalar() or 0
    
    velocity_sp_per_week = points_done_last_14 / 2.0
    
    sprints_remaining = int((remaining_points / (velocity_sp_per_week * 2)) + 1) if velocity_sp_per_week > 0 else None
    
    confidence = "HIGH" if tasks_done_last_14 > 5 else "LOW"
    risk_level = "HIGH" if velocity_tasks_per_week < 1 and remaining_tasks > 10 else "LOW"

    return ProjectForecast(
        project_id=project_id,
        estimated_completion_date=estimated_completion_date,
        remaining_tasks=remaining_tasks,
        completed_tasks=completed_tasks,
        completion_rate=completion_rate,
        velocity=velocity_tasks_per_week,
        remaining_story_points=remaining_points,
        estimated_sprints_remaining=sprints_remaining,
        confidence=confidence,
        risk_level=risk_level,
        assumptions=ForecastAssumptions(
            velocity_tasks_per_week=velocity_tasks_per_week,
            velocity_story_points_per_week=velocity_sp_per_week,
            historical_weeks_analyzed=2,
            unestimated_tasks=db.query(Task).filter(Task.project_id == project_id, Task.estimate_points == None, Task.status != 'DONE').count()
        )
    )

def calculate_project_risks(db: Session, project_id: UUID, org_id: UUID) -> ProjectRiskEngineResult:
    risks = []
    now = datetime.now(timezone.utc)
    
    # Overdue tasks
    overdue_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status != 'DONE',
        Task.due_date < now
    ).all()
    
    if overdue_tasks:
        risks.append(RiskItem(
            category="SCHEDULE", severity="HIGH" if len(overdue_tasks) > 3 else "MEDIUM",
            score=min(len(overdue_tasks) * 10, 30),
            title=f"{len(overdue_tasks)} Overdue Tasks",
            explanation="There are tasks past their due date.",
            evidence=f"Tasks including {overdue_tasks[0].title} are overdue.",
            recommendation="Review overdue tasks and reassign or adjust deadlines."
        ))
        
    # Deployment failures
    recent_deployments = db.query(Deployment).filter(
        Deployment.project_id == project_id
    ).order_by(Deployment.created_at.desc()).limit(5).all()
    
    failed_deps = [d for d in recent_deployments if d.status == 'FAILED']
    if len(failed_deps) >= 2:
        risks.append(RiskItem(
            category="INFRASTRUCTURE", severity="CRITICAL", score=40,
            title="Recurring Deployment Failures",
            explanation="Recent deployments have failed.",
            evidence=f"{len(failed_deps)} of the last 5 deployments failed.",
            recommendation="Investigate deployment logs and stabilize the pipeline."
        ))
        
    # Blocked tasks
    blocked_tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_blocked == True).count()
    if blocked_tasks > 0:
        risks.append(RiskItem(
            category="WORKFLOW", severity="HIGH", score=20,
            title=f"{blocked_tasks} Blocked Tasks",
            explanation="Tasks are actively blocked.",
            evidence=f"{blocked_tasks} tasks currently marked as BLOCKED.",
            recommendation="Swarm on blocked tasks to unblock the team."
        ))
        
    total_score = sum(r.score for r in risks)
    if total_score > 60: risk_level = "CRITICAL"
    elif total_score > 40: risk_level = "HIGH"
    elif total_score > 20: risk_level = "MEDIUM"
    else: risk_level = "LOW"
    
    return ProjectRiskEngineResult(
        overall_risk_score=min(total_score, 100),
        risk_level=risk_level,
        risks=risks
    )

def calculate_sprint_plan(db: Session, project_id: UUID, org_id: UUID) -> SprintCapacityRecommendation:
    # Very basic deterministic logic
    backlog = db.query(Task).filter(Task.project_id == project_id, Task.status == 'TODO', Task.sprint_id == None).all()
    team_members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).count()
    
    capacity = team_members * 10.0 # 10 points per member
    
    suggested = []
    excluded = []
    reasons = {}
    current_load = 0
    
    # Sort by priority
    priority_map = {"URGENT": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    backlog.sort(key=lambda x: priority_map.get(x.priority, 0), reverse=True)
    
    for t in backlog:
        pts = t.estimate_points or 3.0
        if current_load + pts <= capacity:
            suggested.append(t.id)
            current_load += pts
        else:
            excluded.append(t.id)
            reasons[str(t.id)] = "Exceeds calculated team capacity for this sprint."
            
    return SprintCapacityRecommendation(
        recommended_capacity_points=capacity,
        suggested_tasks=suggested,
        excluded_tasks=excluded,
        reasons_for_exclusions=reasons,
        overloaded_members=[],
        dependency_warnings=[],
        confidence="MEDIUM"
    )

def calculate_task_priorities(db: Session, project_id: UUID, org_id: UUID) -> List[TaskPriorityScore]:
    tasks = db.query(Task).filter(Task.project_id == project_id, Task.status != 'DONE').all()
    results = []
    now = datetime.now(timezone.utc)
    
    priority_weights = {"URGENT": 40, "HIGH": 30, "MEDIUM": 20, "LOW": 10}
    
    for t in tasks:
        score = priority_weights.get(t.priority, 10)
        reasons = []
        
        if t.due_date:
            days_until = (t.due_date - now).days
            if days_until < 0:
                score += 30
                reasons.append("Task is overdue.")
            elif days_until < 3:
                score += 15
                reasons.append("Due date is approaching soon.")
                
        if t.is_blocked == True:
            score -= 10
            reasons.append("Task is blocked, cannot proceed immediately.")
            
        # Age
        age_days = (now - t.created_at).days
        if age_days > 30:
            score += 5
            reasons.append("Task is old, consider completing or discarding.")
            
        results.append(TaskPriorityScore(
            task_id=t.id,
            task_key=t.task_key,
            score=float(score),
            priority_level="HIGH" if score > 50 else ("MEDIUM" if score > 25 else "LOW"),
            reasons=reasons
        ))
        
    results.sort(key=lambda x: x.score, reverse=True)
    return results

def get_org_daily_brief(db: Session, org_id: UUID) -> Dict[str, Any]:
    # Gathering org-level data deterministically for the brief
    # In reality we might use AI to format, but deterministic rules are required by prompt for "Each recommendation must contain evidence."
    now = datetime.now(timezone.utc)
    
    overdue_tasks = db.query(Task).join(Project).filter(Project.organization_id == org_id, Task.status != 'DONE', Task.due_date < now).limit(5).all()
    blocked_tasks = db.query(Task).join(Project).filter(Project.organization_id == org_id, Task.is_blocked == True).limit(5).all()
    failed_jobs = [] # Not directly queried here for brevity
    
    return {
        "projects_needing_attention": [],
        "overdue_tasks": [{"title": t.title, "priority": t.priority, "reason": "Due date passed", "source": "task"} for t in overdue_tasks],
        "blocked_tasks": [{"title": t.title, "priority": t.priority, "reason": "Status is BLOCKED", "source": "task"} for t in blocked_tasks],
        "sprint_deadlines": [],
        "deployment_failures": [],
        "important_github_activity": [],
        "security_events": [],
        "failed_background_jobs": [],
        "high_priority_notifications": [],
        "recommended_focus_for_today": [
            {"title": "Unblock critical tasks", "priority": "HIGH", "reason": f"{len(blocked_tasks)} tasks are blocked.", "source": "tasks"}
        ] if blocked_tasks else []
    }
