from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case
from typing import Any, List, Optional
from datetime import datetime, timezone

from app.api import deps
from uuid import UUID
from fastapi import HTTPException
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskStats
from app.models.organization import OrganizationRole
from app.models.security import Role

router = APIRouter()

@router.get("/stats", response_model=TaskStats)
def get_dashboard_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)

    # Phase 31: previously 6 separate COUNT queries over the same join;
    # collapse into a single aggregate pass.
    now = datetime.now(timezone.utc)
    row = db.query(
        func.count().label("total"),
        func.sum(case((Task.status == TaskStatus.TODO, 1), else_=0)).label("todo"),
        func.sum(case((Task.status == TaskStatus.IN_PROGRESS, 1), else_=0)).label("in_progress"),
        func.sum(case((Task.status == TaskStatus.IN_REVIEW, 1), else_=0)).label("in_review"),
        func.sum(case((Task.status == TaskStatus.DONE, 1), else_=0)).label("done"),
        func.sum(case(((Task.status != TaskStatus.DONE) & (Task.due_date < now), 1), else_=0)).label("overdue"),
    ).join(Project).filter(Project.organization_id == org_id).one()

    return TaskStats(
        total=row.total or 0,
        todo=row.todo or 0,
        in_progress=row.in_progress or 0,
        in_review=row.in_review or 0,
        done=row.done or 0,
        overdue=row.overdue or 0
    )

from app.models.sprint import Sprint, SprintStatus

@router.get("/sprints/active")
def get_active_sprints(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)
    
    sprints = db.query(Sprint).options(joinedload(Sprint.project)).join(Project).filter(
        Project.organization_id == org_id,
        Sprint.status == SprintStatus.ACTIVE
    ).all()

    # Phase 31: single grouped query instead of 2 aggregates per sprint (N+1).
    sprint_ids = [s.id for s in sprints]
    agg: dict = {}
    if sprint_ids:
        rows = db.query(
            Task.sprint_id, Task.status, func.sum(Task.estimate_points)
        ).filter(Task.sprint_id.in_(sprint_ids)).group_by(Task.sprint_id, Task.status).all()
        for sprint_id, status, pts in rows:
            bucket = agg.setdefault(sprint_id, {"total": 0.0, "done": 0.0})
            bucket["total"] += float(pts or 0)
            if status == TaskStatus.DONE:
                bucket["done"] += float(pts or 0)

    result = []
    for s in sprints:
        bucket = agg.get(s.id, {"total": 0.0, "done": 0.0})
        total_pts = bucket["total"]
        completed_pts = bucket["done"]
        
        result.append({
            "id": s.id,
            "project_name": s.project.name,
            "sprint_name": s.name,
            "key": s.key,
            "end_date": s.end_date,
            "total_points": total_pts,
            "completed_points": completed_pts,
            "progress": (completed_pts / total_pts * 100) if total_pts > 0 else 0
        })
    return result


# ---------------------------------------------------------------------------
# Phase 45 — personal dashboard layout (widget show/hide + ordering)
# ---------------------------------------------------------------------------

from app.models.dashboard import DashboardLayout
from app.schemas.report import DashboardLayoutSave, DashboardLayoutResponse

# Server-authoritative widget registry. The frontend mirrors these IDs; the
# backend is the security boundary — widgets a user lacks permission for are
# filtered out of every response and silently dropped from saved layouts.
WIDGET_REGISTRY = {
    "stats": {"title": "Overview Stats", "required_permission": "analytics.view"},
    "active_sprints": {"title": "Active Sprints", "required_permission": None},
    "recent_projects": {"title": "Recent Projects", "required_permission": None},
}
DEFAULT_LAYOUT = ["stats", "active_sprints", "recent_projects"]
MAX_LAYOUT_ITEMS = 50


def _has_widget_permission(db: Session, member, permission: Optional[str]) -> bool:
    """Non-raising variant of reports.check_permission for widget filtering."""
    if not permission:
        return True
    if member.role in (OrganizationRole.OWNER, OrganizationRole.ADMIN):
        return True
    if member.custom_role_id:
        role = db.query(Role).filter(Role.id == member.custom_role_id).first()
        if role:
            perms = {rp.permission for rp in role.permissions}
            return permission in perms
    return False


def _default_widgets_for(db: Session, member) -> List[dict]:
    return [
        {"id": wid, "visible": True}
        for wid in DEFAULT_LAYOUT
        if wid in WIDGET_REGISTRY
        and _has_widget_permission(db, member, WIDGET_REGISTRY[wid]["required_permission"])
    ]


def _clean_layout(db: Session, member, widgets: List[dict]) -> List[dict]:
    """Drop unknown/stale widget IDs, duplicates and widgets the user may not
    see. Keeps the caller's order and visibility flags; adds ids missing from
    the registry nowhere (they are simply gone)."""
    seen = set()
    cleaned = []
    for item in widgets:
        wid = item.get("id")
        if wid not in WIDGET_REGISTRY or wid in seen:
            continue
        if not _has_widget_permission(db, member, WIDGET_REGISTRY[wid]["required_permission"]):
            continue
        seen.add(wid)
        cleaned.append({"id": wid, "visible": bool(item.get("visible", True))})
    return cleaned


def _load_or_default(db: Session, current_user, org_id: UUID) -> tuple:
    member = deps.require_organization_member(db, current_user.id, org_id)
    saved = db.query(DashboardLayout).filter(
        DashboardLayout.user_id == current_user.id,
        DashboardLayout.organization_id == org_id,
    ).first()
    return member, (saved.layout if saved else None), saved


@router.get("/layout", response_model=DashboardLayoutResponse)
def get_dashboard_layout(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member, saved, _row = _load_or_default(db, current_user, org_id)
    if saved is None:
        return DashboardLayoutResponse(
            widgets=_default_widgets_for(db, member),
            defaults=DEFAULT_LAYOUT,
            customized=False,
        )
    # Stale/unknown widget IDs are ignored safely on read.
    return DashboardLayoutResponse(
        widgets=_clean_layout(db, member, saved),
        defaults=DEFAULT_LAYOUT,
        customized=True,
    )


@router.put("/layout", response_model=DashboardLayoutResponse)
def save_dashboard_layout(
    *,
    layout_in: DashboardLayoutSave,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    if len(layout_in.widgets) > MAX_LAYOUT_ITEMS:
        raise HTTPException(status_code=422, detail=f"Layout cannot contain more than {MAX_LAYOUT_ITEMS} widgets")
    member, _, row = _load_or_default(db, current_user, org_id)
    cleaned = _clean_layout(db, member, [w.model_dump() for w in layout_in.widgets])
    if row is None:
        row = DashboardLayout(user_id=current_user.id, organization_id=org_id)
        db.add(row)
    row.layout = cleaned
    db.commit()
    return DashboardLayoutResponse(widgets=cleaned, defaults=DEFAULT_LAYOUT, customized=True)


@router.delete("/layout", response_model=DashboardLayoutResponse)
def reset_dashboard_layout(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member, _, row = _load_or_default(db, current_user, org_id)
    if row is not None:
        db.delete(row)
        db.commit()
    return DashboardLayoutResponse(
        widgets=_default_widgets_for(db, member),
        defaults=DEFAULT_LAYOUT,
        customized=False,
    )
