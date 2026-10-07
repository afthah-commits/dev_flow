"""Phase 47 — AI-assisted planning & estimation service.

ADVISORY ONLY. Everything here produces a preview for explicit user review;
nothing in this module creates, updates, or schedules anything.

The deterministic parts (complexity, estimation, risks, capacity) are computed
from existing project/task/sprint data with plain heuristics so MockAIProvider
tests are fully deterministic. Only the suggested task breakdown goes through
the existing AIProvider abstraction (MockAIProvider / OpenAIProvider), and its
output is strictly sanitized and bounded before being returned.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.sprint import Sprint
from app.models.task import Task, TaskStatus, TaskDependency, TaskDependencyType
from app.schemas.ai import (
    AIPlanningAnalysis,
    AIPlanningCapacity,
    AIPlanningSuggestion,
)
from app.services.ai.base import AIProvider
from app.services.ai.service import SYSTEM_PROMPT

MAX_SUGGESTIONS = 8
MAX_TITLE_LEN = 200
MAX_DESC_LEN = 1000
MAX_PROMPT_TEXT = 500
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "URGENT"}

DONE_STATUSES = {TaskStatus.DONE}


class _BreakdownSchema(BaseModel):
    """json_schema contract for the provider. Property name `subtasks`
    matches the existing TaskBreakdown contract reused by MockAIProvider."""

    subtasks: List[AIPlanningSuggestion]


def _task_text(task: Optional[Task]) -> str:
    if not task:
        return "the project's upcoming work"
    desc = (task.description or "").strip()
    text = f"{task.title}\n{desc}" if desc else task.title
    return text[:MAX_PROMPT_TEXT]


def sanitize_suggestions(raw: object) -> List[AIPlanningSuggestion]:
    """Strictly validate/bound AI output. Plain strings only — no executable
    configuration, no nested structures, bounded lengths and count."""
    if not isinstance(raw, dict):
        return []
    items = raw.get("subtasks")
    if not isinstance(items, list):
        return []
    out: List[AIPlanningSuggestion] = []
    for item in items[:MAX_SUGGESTIONS]:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        desc = item.get("description")
        if not isinstance(desc, str):
            desc = ""
        priority = item.get("priority")
        if not isinstance(priority, str) or priority.upper() not in VALID_PRIORITIES:
            priority = "MEDIUM"
        out.append(
            AIPlanningSuggestion(
                title=title.strip()[:MAX_TITLE_LEN],
                description=desc.strip()[:MAX_DESC_LEN],
                priority=priority.upper(),
            )
        )
        if len(out) >= MAX_SUGGESTIONS:
            break
    return out


def compute_complexity(task: Task, blocked_count: int, checklist_count: int) -> tuple[str, List[str]]:
    factors: List[str] = []
    score = 1
    desc_len = len((task.description or "").strip())
    if desc_len >= 400:
        score += 2
        factors.append("long description")
    elif desc_len >= 150:
        score += 1
        factors.append("detailed description")
    if checklist_count >= 5:
        score += 2
        factors.append(f"{checklist_count} checklist items")
    elif checklist_count >= 2:
        score += 1
        factors.append(f"{checklist_count} checklist items")
    if blocked_count:
        score += 2
        factors.append(f"{blocked_count} blocking dependencies")
    if (task.priority or TaskPriority_value(task)).name in ("HIGH", "URGENT"):
        score += 1
        factors.append("high priority")
    complexity = "HIGH" if score >= 5 else ("MEDIUM" if score >= 3 else "LOW")
    if not factors:
        factors.append("small, well-scoped task")
    return complexity, factors


def TaskPriority_value(task: Task):
    return task.priority if task.priority is not None else TaskPriority.MEDIUM


def compute_estimate(
    task: Task, complexity: str, subtask_count: int, blocked_count: int
) -> tuple[float, str, List[str]]:
    """Story points — the convention already used by Task.estimate_points."""
    base = {"LOW": 2.0, "MEDIUM": 5.0, "HIGH": 8.0}[complexity]
    estimate = base + subtask_count + blocked_count
    estimate = float(min(estimate, 21))
    factors = [f"complexity {complexity}"]
    if subtask_count:
        factors.append(f"{subtask_count} existing subtasks")
    if blocked_count:
        factors.append(f"{blocked_count} blocking dependencies")
    if task.estimate_points is not None:
        confidence = "HIGH"
        factors.append(f"existing manual estimate ({task.estimate_points:g} points)")
    elif (task.description or "").strip():
        confidence = "MEDIUM"
        factors.append("description available")
    else:
        confidence = "LOW"
        factors.append("no description or manual estimate")
    return estimate, confidence, factors


def compute_capacity(db: Session, task: Optional[Task], org_id: UUID) -> Optional[AIPlanningCapacity]:
    """Reuse existing sprint data (Sprint.capacity + task estimate_points).
    Returns INSUFFICIENT_DATA status when required data is missing."""
    sprint: Optional[Sprint] = None
    if task is not None and task.sprint_id:
        sprint = db.query(Sprint).filter(Sprint.id == task.sprint_id).first()
    if sprint is None or sprint.capacity is None:
        return AIPlanningCapacity(status="INSUFFICIENT_DATA")

    sprint_tasks = (
        db.query(Task.estimate_points, Task.status)
        .filter(Task.sprint_id == sprint.id)
        .all()
    )
    committed = sum(
        float(pts or 0)
        for pts, status in sprint_tasks
        if status not in DONE_STATUSES
    )
    remaining = float(sprint.capacity) - committed
    if task is not None and task.sprint_id == sprint.id and task.status not in DONE_STATUSES:
        # The analyzed task is already part of the committed load.
        pass
    status = "OK"
    if remaining < 0:
        status = "OVER_CAPACITY"
    return AIPlanningCapacity(
        status=status,
        sprint_id=sprint.id,
        sprint_name=sprint.name,
        capacity_points=float(sprint.capacity),
        committed_points=round(committed, 2),
        remaining_points=round(remaining, 2),
    )


async def build_planning_analysis(
    db: Session,
    project: Project,
    task: Optional[Task],
    provider: AIProvider,
    org_id: UUID,
) -> AIPlanningAnalysis:
    """Assemble the advisory analysis. No DB writes."""

    blocked_count = (
        db.query(TaskDependency)
        .filter(
            TaskDependency.source_id == task.id,
            TaskDependency.dependency_type == TaskDependencyType.BLOCKS,
        )
        .count()
        if task
        else 0
    )
    checklist_count = len(task.checklists) if task else 0
    subtask_count = len(task.subtasks) if task else 0

    dependency_concerns: List[str] = []
    if task and blocked_count:
        blockers = (
            db.query(Task)
            .join(TaskDependency, TaskDependency.target_id == Task.id)
            .filter(
                TaskDependency.source_id == task.id,
                TaskDependency.dependency_type == TaskDependencyType.BLOCKS,
            )
            .all()
        )
        for blocker in blockers[:5]:
            if blocker.status not in DONE_STATUSES:
                dependency_concerns.append(
                    f"Blocked by unfinished task {blocker.task_key or blocker.id}: {blocker.title}"
                )

    complexity, complexity_factors = compute_complexity(task, blocked_count, checklist_count) if task \
        else ("MEDIUM", ["project-level analysis"])
    estimate, confidence, estimate_factors = compute_estimate(task, complexity, subtask_count, blocked_count) \
        if task else (5.0, "LOW", ["project-level estimate"])

    risks: List[str] = []
    missing_information: List[str] = []
    if task:
        if task.assignee_id is None:
            missing_information.append("No assignee")
        if task.due_date is None:
            missing_information.append("No due date")
        if task.estimate_points is None:
            missing_information.append("No manual estimate set")
        if not (task.description or "").strip():
            missing_information.append("No description")
        if task.due_date and task.status not in DONE_STATUSES:
            from datetime import datetime, timezone
            if task.due_date < datetime.now(timezone.utc):
                risks.append("Task is overdue")
        if blocked_count:
            risks.append(f"{blocked_count} blocking dependencies")
        if complexity == "HIGH" and checklist_count == 0:
            risks.append("High complexity with no checklist")
    else:
        missing_information.append("No specific task selected — analysis is project-level")

    # Breakdown suggestions through the existing AI provider abstraction.
    prompt = (
        "Suggest a short task breakdown (subtasks) for planning purposes only. "
        f"Task:\n{_task_text(task)}"
    )
    async def _provider_breakdown() -> object:
        return await provider.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SYSTEM_PROMPT,
            json_schema=_BreakdownSchema.model_json_schema(),
        )

    try:
        raw = await _provider_breakdown()
    except Exception:
        raw = {}
    import json as _json

    try:
        data = _json.loads(raw) if isinstance(raw, str) else (raw or {})
    except Exception:
        data = {}
    suggestions = sanitize_suggestions(data)

    capacity = compute_capacity(db, task, org_id)

    if task and capacity and capacity.status == "OVER_CAPACITY":
        risks.append(
            f"Sprint {capacity.sprint_name} is over capacity "
            f"(remaining {capacity.remaining_points} points)"
        )

    return AIPlanningAnalysis(
        task_id=task.id if task else None,
        project_id=project.id,
        complexity=complexity,
        complexity_factors=complexity_factors,
        estimate_points=estimate,
        estimate_confidence=confidence,
        estimate_factors=estimate_factors,
        risks=risks,
        missing_information=missing_information,
        dependency_concerns=dependency_concerns,
        suggested_breakdown=suggestions,
        capacity=capacity,
        advisory=True,
        provider=type(provider).__name__,
    )
