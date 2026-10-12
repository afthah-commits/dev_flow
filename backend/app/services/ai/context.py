from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.sprint import Sprint, SprintStatus
from app.models.organization import OrganizationMember

async def build_project_context(db: Session, project_id: UUID, user_id: UUID) -> str:
    """Builds a rich, fast, authorized context string for the specified project.

    Queries local database with organization isolation. Avoids external network calls
    to prevent slow latency.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return "No project context available."

    tech_stack_str = ", ".join(project.tech_stack) if project.tech_stack else "None specified"
    context = (
        f"PROJECT CONTEXT:\n"
        f"Name: {project.name} (Key: {project.key or 'N/A'})\n"
        f"Status: {project.status} | Priority: {project.priority}\n"
        f"Description: {project.description or 'None'}\n"
        f"Tech Stack: {tech_stack_str}\n"
    )

    # Active sprint
    active_sprint = db.query(Sprint).filter(
        Sprint.project_id == project_id,
        Sprint.status == SprintStatus.ACTIVE
    ).first()
    if active_sprint:
        end_str = active_sprint.end_date.strftime('%Y-%m-%d') if active_sprint.end_date else 'No end date'
        context += f"Active Sprint: {active_sprint.name} (Goal: {active_sprint.goal or 'None'}, Ends: {end_str})\n"

    # Tasks breakdown
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    total = len(tasks)
    done_tasks = [t for t in tasks if t.status == TaskStatus.DONE]
    in_prog_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
    now = datetime.now(timezone.utc)
    overdue_tasks = [
        t for t in tasks
        if t.status != TaskStatus.DONE and t.due_date and (t.due_date if t.due_date.tzinfo else t.due_date.replace(tzinfo=timezone.utc)) < now
    ]

    context += (
        f"\nTASK METRICS:\n"
        f"Total: {total} | Completed: {len(done_tasks)} | In Progress: {len(in_prog_tasks)} | Overdue: {len(overdue_tasks)}\n"
    )

    # Overdue tasks
    if overdue_tasks:
        context += "\nOVERDUE TASKS:\n"
        for t in overdue_tasks[:8]:
            due_str = t.due_date.strftime('%Y-%m-%d') if t.due_date else 'Unknown'
            assignee_str = t.assignee.name if t.assignee else 'Unassigned'
            context += f"- [{t.task_key or t.id}] {t.title} (Priority: {t.priority.value}, Due: {due_str}, Assignee: {assignee_str})\n"

    # In-progress & high-priority active tasks
    active_tasks = [t for t in tasks if t.status in (TaskStatus.IN_PROGRESS, TaskStatus.TODO) and t not in overdue_tasks]
    priority_order = {TaskPriority.CRITICAL: 0, TaskPriority.HIGH: 1, TaskPriority.MEDIUM: 2, TaskPriority.LOW: 3}
    active_tasks.sort(key=lambda t: priority_order.get(t.priority, 2))

    if active_tasks:
        context += "\nACTIVE TASKS:\n"
        for t in active_tasks[:10]:
            assignee_str = t.assignee.name if t.assignee else 'Unassigned'
            due_str = f", Due: {t.due_date.strftime('%Y-%m-%d')}" if t.due_date else ""
            context += f"- [{t.task_key or t.id}] ({t.status.value}) {t.title} [Priority: {t.priority.value}{due_str}, Assignee: {assignee_str}]\n"

    # Team members in organization
    members = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == project.organization_id
    ).all()
    if members:
        member_names = [m.user.name for m in members if m.user and m.user.name]
        if member_names:
            context += f"\nTEAM MEMBERS: {', '.join(member_names[:8])}\n"

    return context


def build_organization_context(db: Session, org_id: UUID, user_id: UUID) -> str:
    """Builds a summary of organization projects for global chat conversations."""
    projects = db.query(Project).filter(Project.organization_id == org_id).all()
    if not projects:
        return "ORGANIZATION CONTEXT: No projects created yet."

    now = datetime.now(timezone.utc)
    lines = ["ORGANIZATION PROJECTS:"]
    for p in projects[:10]:
        total = db.query(Task).filter(Task.project_id == p.id).count()
        overdue = db.query(Task).filter(
            Task.project_id == p.id,
            Task.status != TaskStatus.DONE,
            Task.due_date < now
        ).count()
        lines.append(f"- '{p.name}' (Key: {p.key}, ID: {p.id}): {total} tasks ({overdue} overdue), Status: {p.status}")

    return "\n".join(lines) + "\n"
