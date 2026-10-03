from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from uuid import UUID
from app.models.project import Project
from app.models.task import Task
from app.models.github import ProjectGitHubRepository

def get_dashboard_overview(db: Session, org_id: UUID) -> dict:
    projects = db.query(Project).filter(Project.organization_id == org_id).all()
    total_projects = len(projects)
    active_projects = sum(1 for p in projects if p.status == "ACTIVE")
    completed_projects = sum(1 for p in projects if p.status == "COMPLETED")
    
    project_ids = [p.id for p in projects]
    tasks = db.query(Task).filter(Task.project_id.in_(project_ids)).all() if project_ids else []
    
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "DONE")
    in_progress_tasks = sum(1 for t in tasks if t.status == "IN_PROGRESS")
    
    now = datetime.now(timezone.utc)
    overdue_tasks = sum(1 for t in tasks if t.due_date and t.due_date.replace(tzinfo=timezone.utc) < now and t.status != "DONE")

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "overdue_tasks": overdue_tasks,
        "open_github_prs": 0,
        "open_github_issues": 0
    }

def calculate_project_health(db: Session, project_id: UUID) -> dict:
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    if not tasks:
        return {"score": 100, "status": "Healthy"}
        
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "DONE")
    
    now = datetime.now(timezone.utc)
    overdue = sum(1 for t in tasks if t.due_date and t.due_date.replace(tzinfo=timezone.utc) < now and t.status != "DONE")
    
    score = 100
    score -= (overdue / total) * 40
    
    high_incomplete = sum(1 for t in tasks if t.priority in ["HIGH", "CRITICAL"] and t.status != "DONE")
    score -= (high_incomplete / total) * 20
    
    score += (completed / total) * 20
    
    score = max(0, min(100, int(score)))
    
    status = "Healthy"
    if score < 50:
        status = "At Risk"
    elif score < 80:
        status = "Attention"
        
    return {"score": score, "status": status}

def get_project_analytics(db: Session, project_id: UUID) -> dict:
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    total_tasks = len(tasks)
    completed = sum(1 for t in tasks if t.status == "DONE")
    in_progress = sum(1 for t in tasks if t.status == "IN_PROGRESS")
    
    now = datetime.now(timezone.utc)
    overdue = sum(1 for t in tasks if t.due_date and t.due_date.replace(tzinfo=timezone.utc) < now and t.status != "DONE")
    
    completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
    
    health = calculate_project_health(db, project_id)
    
    status_counts = {}
    priority_counts = {}
    for t in tasks:
        status_counts[t.status] = status_counts.get(t.status, 0) + 1
        priority_counts[t.priority] = priority_counts.get(t.priority, 0) + 1
        
    status_distribution = [{"status": k, "count": v} for k, v in status_counts.items()]
    priority_distribution = [{"priority": k, "count": v} for k, v in priority_counts.items()]
    
    # Deadlines
    due_today = 0
    due_soon = 0
    future = 0
    no_deadline = 0
    
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    for t in tasks:
        if not t.due_date:
            no_deadline += 1
            continue
        if t.status == "DONE":
            continue
            
        due = t.due_date.replace(tzinfo=timezone.utc)
        if due < now:
            continue # overdue already counted
        elif due < today_start + timedelta(days=1):
            due_today += 1
        elif due < today_start + timedelta(days=4):
            due_soon += 1
        else:
            future += 1
            
    deadlines = {
        "overdue": overdue,
        "due_today": due_today,
        "due_soon": due_soon,
        "future": future,
        "no_deadline": no_deadline
    }
    
    # Trends (mocked simple trend based on created tasks)
    trends = []
    for i in range(6, -1, -1):
        d = (now - timedelta(days=i)).date()
        trends.append({
            "date": d.isoformat(),
            "created": sum(1 for t in tasks if t.created_at.date() == d),
            "completed": sum(1 for t in tasks if t.updated_at and t.updated_at.date() == d and t.status == "DONE"),
            "overdue": 0
        })

    return {
        "completion_rate": completion_rate,
        "total_tasks": total_tasks,
        "completed": completed,
        "in_progress": in_progress,
        "overdue": overdue,
        "health": health,
        "status_distribution": status_distribution,
        "priority_distribution": priority_distribution,
        "deadlines": deadlines,
        "trends": trends
    }
