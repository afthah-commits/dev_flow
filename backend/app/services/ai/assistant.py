import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User
from app.models.organization import OrganizationMember
from app.models.ai_conversation import AIConversation
from app.api import deps
from app.services.audit_service import record_event

# ---------------------------------------------------------------------------
# Natural Language Relative Date Parser
# ---------------------------------------------------------------------------

WEEKDAYS = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

def resolve_relative_date(text: str, base_date: Optional[datetime] = None) -> Optional[datetime]:
    """Resolves relative date references like 'tomorrow', 'Friday', 'next Monday',

    'end of week', or explicit ISO dates to a timezone-aware datetime at 23:59:59 UTC.
    """
    if not text:
        return None

    if base_date is None:
        base_date = datetime.now(timezone.utc)
    elif base_date.tzinfo is None:
        base_date = base_date.replace(tzinfo=timezone.utc)

    text_lower = text.lower()

    # 1. Explicit ISO date match: YYYY-MM-DD
    iso_match = re.search(r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b', text_lower)
    if iso_match:
        try:
            year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            return datetime(year, month, day, 23, 59, 59, tzinfo=timezone.utc)
        except ValueError:
            pass

    # 2. "today"
    if re.search(r'\b(today|by today)\b', text_lower):
        return base_date.replace(hour=23, minute=59, second=59, microsecond=0)

    # 3. "tomorrow"
    if re.search(r'\b(tomorrow|by tomorrow)\b', text_lower):
        target = base_date + timedelta(days=1)
        return target.replace(hour=23, minute=59, second=59, microsecond=0)

    # 4. "in X days"
    days_match = re.search(r'\bin\s+(\d+)\s+days?\b', text_lower)
    if days_match:
        days = int(days_match.group(1))
        target = base_date + timedelta(days=days)
        return target.replace(hour=23, minute=59, second=59, microsecond=0)

    # 5. "end of week" / "by end of week" -> Friday of current week
    if "end of week" in text_lower or "end of the week" in text_lower:
        current_dow = base_date.weekday()
        days_to_friday = (4 - current_dow) if current_dow <= 4 else (7 - current_dow + 4)
        target = base_date + timedelta(days=days_to_friday)
        return target.replace(hour=23, minute=59, second=59, microsecond=0)

    # 6. "next week" -> Monday of next week
    if "next week" in text_lower and not any(w in text_lower for w in WEEKDAYS):
        current_dow = base_date.weekday()
        days_to_next_mon = 7 - current_dow
        target = base_date + timedelta(days=days_to_next_mon)
        return target.replace(hour=23, minute=59, second=59, microsecond=0)

    # 7. Day of week: "by Friday", "this Friday", "next Friday", "on Friday", "Friday"
    weekday_match = re.search(r'\b(?:by|this|next|on)?\s*(monday|mon|tuesday|tue|tues|wednesday|wed|thursday|thu|thur|thurs|friday|fri|saturday|sat|sunday|sun)\b', text_lower)
    if weekday_match:
        day_word = weekday_match.group(1)
        target_dow = WEEKDAYS[day_word]
        current_dow = base_date.weekday()

        is_next = "next " + day_word in text_lower
        days_ahead = (target_dow - current_dow) % 7
        if days_ahead == 0 or is_next:
            days_ahead += 7

        target = base_date + timedelta(days=days_ahead)
        return target.replace(hour=23, minute=59, second=59, microsecond=0)

    return None


# ---------------------------------------------------------------------------
# Natural Language Task Intent Parser
# ---------------------------------------------------------------------------

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

def parse_task_intent(message: str) -> Optional[Dict[str, Any]]:
    """Analyzes a natural language user message to detect task creation requests

    and extract relevant parameters (count, title, priority, due date, assignee, project).
    """
    msg = message.strip()
    msg_lower = msg.lower()

    # Determine if this is a task creation request
    # Must contain action verbs like create, add, make, open followed by task/tasks
    create_pattern = re.search(
        r'\b(create|add|make|open|schedule|generate)\b\s+(?:(?:a|an|the|\d+|one|two|three|four|five)\s+)?(?:[\w\-]+\s+)*tasks?\b',
        msg_lower
    )
    if not create_pattern:
        return None

    # 1. Task count
    count = 1
    num_match = re.search(r'\b(one|two|three|four|five|\d+)\s+tasks?\b', msg_lower)
    if num_match:
        val = num_match.group(1)
        count = int(val) if val.isdigit() else NUMBER_WORDS.get(val, 1)

    # 2. Priority
    priority = TaskPriority.MEDIUM
    if re.search(r'\b(critical|p0|blocker|urgent blocker)\b', msg_lower):
        priority = TaskPriority.CRITICAL
    elif re.search(r'\b(high[\s\-]priority|urgent|p1|important)\b', msg_lower):
        priority = TaskPriority.HIGH
    elif re.search(r'\b(low[\s\-]priority|minor|p3|trivial)\b', msg_lower):
        priority = TaskPriority.LOW

    # 3. Due Date
    due_date = resolve_relative_date(msg)

    # 4. Assignee extraction (e.g. "assign to Alice", "assigned to john@example.com")
    assignee_query = None
    assignee_match = re.search(r'\b(?:assigned?\s+to|for)\s+([a-zA-Z0-9_\-\.\@]+(?:\s+[a-zA-Z0-9_\-\.\@]+)?)\b', msg, re.IGNORECASE)
    if assignee_match:
        candidate = assignee_match.group(1).strip()
        # Avoid capturing common stop words
        if candidate.lower() not in {"implement", "fix", "friday", "tomorrow", "today", "the", "a", "an", "user"}:
            assignee_query = candidate

    # 5. Project mention extraction (e.g. "in project Mobile App", "for project DevFlow", "in PROJ")
    project_query = None
    proj_match = re.search(r'\b(?:in|for)\s+project\s+([a-zA-Z0-9_\-\s]+?)(?:\s+(?:by|assigned|with|priority)|$)', msg, re.IGNORECASE)
    if proj_match:
        project_query = proj_match.group(1).strip()

    # 6. Extract Task Title
    raw_title = msg
    # Strip leading phrases like "Create a high-priority task to", "Add a task to", "Create three tasks for"
    raw_title = re.sub(
        r'^(?:please\s+)?(?:can\s+you\s+)?(create|add|make|open)\s+(?:(?:a|an|the|\d+|one|two|three|four|five)\s+)?(?:[\w\-]+\s+)*tasks?\s+(?:to|for|called|named|:\s*)?',
        '',
        raw_title,
        flags=re.IGNORECASE
    ).strip()

    # Strip trailing due date clauses like "by Friday", "by tomorrow", "by 2026-10-20"
    raw_title = re.sub(
        r'\s+\b(?:by|due\s+on|before|on)\s+(?:today|tomorrow|friday|monday|tuesday|wednesday|thursday|saturday|sunday|next\s+\w+|end\s+of\s+week|\d{4}-\d{1,2}-\d{1,2})\b.*$',
        '',
        raw_title,
        flags=re.IGNORECASE
    ).strip()

    # Strip trailing assignee clauses like "assigned to John"
    if assignee_query:
        raw_title = re.sub(rf'\s+\b(?:assigned?\s+to|for)\s+{re.escape(assignee_query)}\b.*$', '', raw_title, flags=re.IGNORECASE).strip()

    # Strip trailing project clauses like "in project Backend"
    if project_query:
        raw_title = re.sub(rf'\s+\b(?:in|for)\s+project\s+{re.escape(project_query)}\b.*$', '', raw_title, flags=re.IGNORECASE).strip()

    # Clean punctuation
    raw_title = raw_title.strip(' :;.,-')
    if raw_title:
        # Capitalize first letter
        raw_title = raw_title[0].upper() + raw_title[1:]
    else:
        raw_title = "New Task"

    return {
        "is_create_task": True,
        "count": min(count, 10),
        "title": raw_title,
        "priority": priority,
        "due_date": due_date,
        "assignee_query": assignee_query,
        "project_query": project_query,
    }


# ---------------------------------------------------------------------------
# Project Management Action Handlers
# ---------------------------------------------------------------------------

def execute_create_task(
    db: Session,
    project: Project,
    current_user: User,
    title: str,
    description: Optional[str] = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    due_date: Optional[datetime] = None,
    assignee_id: Optional[UUID] = None,
) -> Task:
    """Creates a task in the database with strict isolation, sequence numbering,

    and audit logging.
    """
    # Verify caller is a member of the project's organization
    deps.require_organization_member(db, current_user.id, project.organization_id)

    # Sequence numbering & task key
    project.task_seq_num += 1
    seq = project.task_seq_num
    task_key = f"{project.key}-{seq}" if project.key else f"PROJ-{seq}"

    task = Task(
        project_id=project.id,
        creator_id=current_user.id,
        task_key=task_key,
        title=title.strip(),
        description=description,
        priority=priority,
        status=TaskStatus.TODO,
        due_date=due_date,
        assignee_id=assignee_id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # Audit logging
    try:
        record_event(
            db=db,
            organization_id=project.organization_id,
            actor_user_id=current_user.id,
            event_type="ai.task_created",
            entity_type="task",
            entity_id=task.id,
            metadata={
                "task_key": task_key,
                "title": task.title,
                "priority": task.priority.value,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            }
        )
    except Exception:
        pass

    return task


def find_target_project(
    db: Session,
    current_user: User,
    org_id: Optional[UUID],
    conv_project_id: Optional[UUID],
    project_query: Optional[str] = None
) -> Tuple[Optional[Project], Optional[str]]:
    """Resolves target project from conversation, project query, or user's organization.

    Returns (project, clarification_message). If ambiguous, project is None and
    clarification_message lists the options.
    """
    # 1. Project specified explicitly by name or key in query
    if project_query:
        q = db.query(Project)
        if org_id:
            q = q.filter(Project.organization_id == org_id)
        candidates = q.all()
        for p in candidates:
            if p.key and p.key.lower() == project_query.lower():
                return p, None
            if p.name and project_query.lower() in p.name.lower():
                return p, None

    # 2. Conversation has project_id
    if conv_project_id:
        proj = db.query(Project).filter(Project.id == conv_project_id).first()
        if proj:
            return proj, None

    # 3. Lookup user's projects in organization
    org_projects_query = db.query(Project)
    if org_id:
        org_projects_query = org_projects_query.filter(Project.organization_id == org_id)
    else:
        # Fallback to user memberships
        memberships = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).all()
        user_org_ids = [m.organization_id for m in memberships]
        org_projects_query = org_projects_query.filter(Project.organization_id.in_(user_org_ids))

    available_projects = org_projects_query.all()

    if not available_projects:
        return None, "No projects found in this workspace. Please create a project first before creating tasks."

    if len(available_projects) == 1:
        return available_projects[0], None

    # Ambiguity: Multiple projects exist and none specified
    options = "\n".join([f"- **{p.name}** (`{p.key or 'NO-KEY'}`)" for p in available_projects[:5]])
    clarification = (
        f"Which project should I add this task to? Please specify the project:\n\n{options}"
    )
    return None, clarification


def resolve_assignee(
    db: Session,
    org_id: UUID,
    assignee_query: Optional[str]
) -> Optional[UUID]:
    """Finds an organization member matching the assignee query."""
    if not assignee_query:
        return None

    members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).all()
    user_ids = [m.user_id for m in members]
    users = db.query(User).filter(User.id.in_(user_ids)).all()

    query_lower = assignee_query.lower()
    for u in users:
        if u.email.lower() == query_lower or query_lower in u.name.lower():
            return u.id

    return None


def handle_show_overdue_tasks(
    db: Session,
    project: Optional[Project],
    org_id: Optional[UUID]
) -> Dict[str, Any]:
    """Retrieves and formats real overdue tasks."""
    now = datetime.now(timezone.utc)
    q = db.query(Task).filter(Task.status != TaskStatus.DONE, Task.due_date < now)

    if project:
        q = q.filter(Task.project_id == project.id)
    elif org_id:
        q = q.join(Project).filter(Project.organization_id == org_id)

    overdue = q.order_by(Task.due_date.asc()).limit(15).all()

    if not overdue:
        return {
            "type": "overdue_tasks",
            "reply": "🎉 **Great news!** There are currently no overdue tasks in this project.",
            "tasks": []
        }

    lines = [f"⚠️ **Found {len(overdue)} Overdue Task(s):**\n"]
    for t in overdue:
        due_str = t.due_date.strftime('%Y-%m-%d') if t.due_date else 'Unknown'
        assignee_str = t.assignee.name if t.assignee else 'Unassigned'
        lines.append(f"- **`{t.task_key or t.id}`** {t.title} — *Due: {due_str}*, Priority: `{t.priority.value}`, Assignee: {assignee_str}")

    lines.append("\n*Tip: Address critical overdue tasks first to keep sprint delivery on schedule.*")
    return {
        "type": "overdue_tasks",
        "reply": "\n".join(lines),
        "tasks": [{"id": str(t.id), "key": t.task_key, "title": t.title} for t in overdue]
    }


def handle_what_to_work_on_today(
    db: Session,
    project: Optional[Project],
    org_id: Optional[UUID],
    current_user: User
) -> Dict[str, Any]:
    """Generates an actionable daily work plan from in-progress, overdue, and high-priority tasks."""
    now = datetime.now(timezone.utc)
    base_q = db.query(Task).filter(Task.status != TaskStatus.DONE)
    if project:
        base_q = base_q.filter(Task.project_id == project.id)
    elif org_id:
        base_q = base_q.join(Project).filter(Project.organization_id == org_id)

    tasks = base_q.all()

    # 1. In-progress work
    in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
    # 2. Overdue work
    overdue = [t for t in tasks if t.due_date and (t.due_date if t.due_date.tzinfo else t.due_date.replace(tzinfo=timezone.utc)) < now]
    # 3. High/Critical priority
    urgent = [t for t in tasks if t.priority in (TaskPriority.CRITICAL, TaskPriority.HIGH) and t not in overdue and t not in in_progress]

    lines = ["📋 **Recommended Daily Focus:**\n"]

    if in_progress:
        lines.append("### 1. In Progress (Finish Before Starting New Work):")
        for t in in_progress[:3]:
            lines.append(f"- **`{t.task_key}`** {t.title} (`{t.priority.value}`)")

    if overdue:
        lines.append("\n### 2. Overdue Items (Immediate Attention):")
        for t in overdue[:3]:
            lines.append(f"- **`{t.task_key}`** {t.title} (Due: {t.due_date.strftime('%Y-%m-%d')})")

    if urgent:
        lines.append("\n### 3. Highest Priority Backlog:")
        for t in urgent[:3]:
            lines.append(f"- **`{t.task_key}`** {t.title} (`{t.priority.value}`)")

    if not in_progress and not overdue and not urgent:
        if tasks:
            lines.append("All active tasks are on schedule! Consider picking up the next task from the backlog:")
            lines.append(f"- **`{tasks[0].task_key}`** {tasks[0].title}")
        else:
            lines.append("No open tasks! The project backlog is clear.")

    return {
        "type": "daily_focus",
        "reply": "\n".join(lines)
    }


def handle_summarize_project(
    db: Session,
    project: Project
) -> Dict[str, Any]:
    """Generates a structured, concise project status summary."""
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    total = len(tasks)
    done = len([t for t in tasks if t.status == TaskStatus.DONE])
    in_prog = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
    now = datetime.now(timezone.utc)
    overdue = len([t for t in tasks if t.status != TaskStatus.DONE and t.due_date and (t.due_date if t.due_date.tzinfo else t.due_date.replace(tzinfo=timezone.utc)) < now])

    completion_rate = round((done / total * 100), 1) if total > 0 else 0.0

    lines = [
        f"📊 **Project Summary: {project.name} (`{project.key}`)**",
        f"- **Status:** `{project.status}` | **Priority:** `{project.priority}`",
        f"- **Tech Stack:** {', '.join(project.tech_stack) if project.tech_stack else 'None specified'}",
        f"- **Completion:** **{completion_rate}%** ({done}/{total} tasks complete)",
        f"- **In Progress:** {in_prog} | **Overdue:** {overdue}",
    ]

    if overdue > 0:
        lines.append(f"\n⚠️ **Attention:** {overdue} overdue task(s) require intervention.")
    else:
        lines.append("\n✅ **Health:** Project delivery velocity is on track.")

    return {
        "type": "project_summary",
        "reply": "\n".join(lines)
    }


def handle_explain_delay(
    db: Session,
    project: Project
) -> Dict[str, Any]:
    """Analyzes reasons for project delay based on real overdue and blocked tasks."""
    now = datetime.now(timezone.utc)
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    overdue = [t for t in tasks if t.status != TaskStatus.DONE and t.due_date and (t.due_date if t.due_date.tzinfo else t.due_date.replace(tzinfo=timezone.utc)) < now]
    blocked = [t for t in tasks if getattr(t, 'is_blocked', False) and t.status != TaskStatus.DONE]

    if not overdue and not blocked:
        return {
            "type": "delay_explanation",
            "reply": f"✅ **Project '{project.name}' is currently on track.**\nThere are no overdue or blocked tasks recorded in the system."
        }

    lines = [f"🔍 **Delay Analysis for {project.name}:**\n"]
    if overdue:
        lines.append(f"• **{len(overdue)} Overdue Task(s):**")
        for t in overdue[:5]:
            due_str = t.due_date.strftime('%Y-%m-%d') if t.due_date else 'Unknown'
            assignee = t.assignee.name if t.assignee else 'Unassigned'
            lines.append(f"  - `{t.task_key}` **{t.title}** (Due: {due_str}, Assignee: {assignee})")

    if blocked:
        lines.append(f"\n• **{len(blocked)} Blocked Task(s):**")
        for t in blocked[:5]:
            lines.append(f"  - `{t.task_key}` **{t.title}** is currently blocked.")

    lines.append("\n**Recommended Mitigation:** Reassign unassigned overdue items and clear blockers in the current sprint.")
    return {
        "type": "delay_explanation",
        "reply": "\n".join(lines)
    }


def handle_epic_breakdown(
    db: Session,
    project: Project,
    current_user: User,
    topic: str
) -> Dict[str, Any]:
    """Breaks down a feature or epic into structured subtasks."""
    # Deterministic high-quality subtask generation for feature breakdown
    subtasks = [
        {"title": f"Design & architecture specification for {topic}", "priority": TaskPriority.HIGH},
        {"title": f"Implement backend service and database models for {topic}", "priority": TaskPriority.HIGH},
        {"title": f"Build frontend user interface and state integration for {topic}", "priority": TaskPriority.MEDIUM},
        {"title": f"Write automated unit & integration tests for {topic}", "priority": TaskPriority.MEDIUM},
    ]

    lines = [
        f"🧩 **Decomposition Plan for: {topic}**\n",
        "Suggested breakdown into 4 engineering tasks:\n"
    ]
    for i, st in enumerate(subtasks, 1):
        lines.append(f"{i}. **{st['title']}** (Priority: `{st['priority'].value}`)")

    lines.append("\n*To automatically create these tasks, reply:* **'Create these tasks'**")

    return {
        "type": "epic_breakdown",
        "reply": "\n".join(lines),
        "suggestions": subtasks
    }


# ---------------------------------------------------------------------------
# Main Assistant Orchestrator
# ---------------------------------------------------------------------------

async def process_project_assistant_request(
    db: Session,
    conversation: AIConversation,
    current_user: User,
    message: str,
    org_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """Evaluates user message for natural language project management intents.

    Executes authorized backend actions (task creation, overdue inspection, etc.).
    Returns structured result dict if handled, or None to fall back to general chat.
    """
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()

    # 1. Intent: CREATE TASK(S)
    task_intent = parse_task_intent(msg_clean)
    if task_intent:
        target_project, clarification = find_target_project(
            db=db,
            current_user=current_user,
            org_id=org_id or getattr(conversation.project, 'organization_id', None),
            conv_project_id=conversation.project_id,
            project_query=task_intent.get("project_query")
        )

        if not target_project:
            return {
                "type": "clarification",
                "reply": clarification or "Please select or specify a project to create this task.",
                "created_tasks": []
            }

        # Resolve assignee if specified
        assignee_id = resolve_assignee(db, target_project.organization_id, task_intent.get("assignee_query"))

        created_tasks: List[Task] = []
        count = task_intent["count"]
        base_title = task_intent["title"]
        priority = task_intent["priority"]
        due_date = task_intent["due_date"]

        try:
            if count == 1:
                task = execute_create_task(
                    db=db,
                    project=target_project,
                    current_user=current_user,
                    title=base_title,
                    description=f"Created via DevFlow AI Assistant from request: '{msg_clean}'",
                    priority=priority,
                    due_date=due_date,
                    assignee_id=assignee_id
                )
                created_tasks.append(task)
            else:
                # Multi-task creation (e.g. "Create three tasks for user authentication")
                # Generate subtask titles
                sub_titles = [
                    f"{base_title} — Part 1: Schema & database models",
                    f"{base_title} — Part 2: Backend API & logic implementation",
                    f"{base_title} — Part 3: Frontend interface & integration",
                    f"{base_title} — Part 4: Automated testing & validation",
                    f"{base_title} — Part 5: Documentation & deployment verification",
                ]
                for i in range(count):
                    st_title = sub_titles[i] if i < len(sub_titles) else f"{base_title} (Task {i+1})"
                    task = execute_create_task(
                        db=db,
                        project=target_project,
                        current_user=current_user,
                        title=st_title,
                        description=f"Subtask {i+1} of {count} created via DevFlow AI Assistant.",
                        priority=priority,
                        due_date=due_date,
                        assignee_id=assignee_id
                    )
                    created_tasks.append(task)
        except Exception as e:
            db.rollback()
            return {
                "type": "error",
                "reply": f"⚠️ Failed to create task: database transaction error. No task was created.",
                "created_tasks": []
            }

        # Build user-facing confirmation response
        if len(created_tasks) == 1:
            t = created_tasks[0]
            due_str = t.due_date.strftime('%Y-%m-%d') if t.due_date else 'No due date set'
            reply = (
                f"✅ **Task Created Successfully**\n\n"
                f"- **Key:** `{t.task_key}`\n"
                f"- **Title:** {t.title}\n"
                f"- **Project:** {target_project.name}\n"
                f"- **Priority:** `{t.priority.value}`\n"
                f"- **Status:** `{t.status.value}`\n"
                f"- **Due Date:** {due_str}\n"
                f"- **Task ID:** `{str(t.id)}`\n"
            )
        else:
            lines = [f"✅ **Successfully Created {len(created_tasks)} Tasks in '{target_project.name}':**\n"]
            for t in created_tasks:
                lines.append(f"- **`{t.task_key}`** {t.title} (`{t.priority.value}`)")
            reply = "\n".join(lines)

        return {
            "type": "task_created",
            "reply": reply,
            "created_tasks": [
                {
                    "id": str(t.id),
                    "key": t.task_key,
                    "title": t.title,
                    "priority": t.priority.value,
                    "status": t.status.value,
                    "project_id": str(target_project.id),
                    "project_name": target_project.name,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                }
                for t in created_tasks
            ]
        }

    # 2. Intent: SHOW OVERDUE TASKS
    if re.search(r'\b(overdue\s+tasks?|what\s+is\s+overdue|show\s+overdue|list\s+overdue)\b', msg_lower):
        proj = conversation.project
        return handle_show_overdue_tasks(db, proj, org_id)

    # 3. Intent: WHAT SHOULD I WORK ON TODAY
    if re.search(r'\b(what\s+should\s+i\s+work\s+on|work\s+on\s+today|what\s+to\s+do\s+today|daily\s+focus|today\'?s?\s+priority)\b', msg_lower):
        proj = conversation.project
        return handle_what_to_work_on_today(db, proj, org_id, current_user)

    # 4. Intent: SUMMARIZE PROJECT
    if re.search(r'\b(summarize\s+(?:my\s+)?(?:current\s+)?project|project\s+summary|status\s+of\s+(?:the\s+)?project)\b', msg_lower):
        if conversation.project:
            return handle_summarize_project(db, conversation.project)

    # 5. Intent: EXPLAIN DELAY
    if re.search(r'\b(why\s+(?:is\s+)?(?:this\s+)?project\s+delayed|explain\s+(?:the\s+)?delay|why\s+are\s+we\s+late)\b', msg_lower):
        if conversation.project:
            return handle_explain_delay(db, conversation.project)

    # 6. Intent: BREAK DOWN EPIC/FEATURE
    breakdown_match = re.search(r'\bbreak\s+(?:down\s+)?(?:the\s+)?(.+?)\s+(?:feature\s+)?into\s+smaller\s+tasks\b', msg_lower)
    if breakdown_match and conversation.project:
        topic = breakdown_match.group(1).strip()
        return handle_epic_breakdown(db, conversation.project, current_user, topic)

    return None
