"""Phase 36 – Advanced Notifications & Action Center API.

All static path segments (/summary, /action-center, /unread-count, /preferences, /read-all)
are declared **before** dynamic /{notification_id} routes to avoid FastAPI shadowing them.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Any, List, Optional
from datetime import datetime, timezone, timedelta
import asyncio

from app.api import deps
from app.models.user import User
from app.models.notification import Notification, NotificationPreference
from app.models.organization import OrganizationMember
from app.schemas.notification import (
    NotificationResponse,
    NotificationPreferenceBase,
    NotificationPreferenceResponse,
    UnreadCountResponse,
    NotificationSummary,
    ActionItemResponse,
)
from app.services.notification_service import (
    get_preferences,
    check_and_generate_overdue_notifications,
    check_and_generate_health_notifications,
    check_and_generate_daily_report_reminder,
    get_user_org_ids,
)

router = APIRouter()


def _deployment_label(dep) -> str:
    """Human-readable label for a Deployment (the model has no `name` column)."""
    for attr in ("deployment_key", "version", "commit_sha"):
        val = getattr(dep, attr, None)
        if val:
            return str(val)
    return str(dep.id)


def _broadcast(event_type: str, notification_id, user_id, **extra) -> None:
    """Fire-and-forget realtime notification event to the owning user."""
    try:
        from app.websockets.manager import manager
        payload = {"type": event_type, "notification_id": str(notification_id),
                   "user_id": str(user_id), **extra}
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(manager.send_personal_message(payload, user_id))
        else:
            loop.run_until_complete(manager.send_personal_message(payload, user_id))
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────────────────
# LIST notifications
# ────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    priority: Optional[str] = None,
    unread_only: bool = False,
    entity_type: Optional[str] = None,
    notification_type: Optional[str] = None,
    important: Optional[bool] = None,
    action_required: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # Lazy-generate task/health/daily-report notifications
    check_and_generate_overdue_notifications(db, current_user.id)
    check_and_generate_health_notifications(db, current_user.id)
    try:
        check_and_generate_daily_report_reminder(db, current_user.id)
    except Exception:
        pass

    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if priority:
        query = query.filter(Notification.priority == priority)
    if unread_only:
        query = query.filter(Notification.read == False)  # noqa: E712
    if entity_type:
        query = query.filter(Notification.entity_type == entity_type)
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    if important is not None:
        query = query.filter(Notification.important == important)
    if action_required is not None:
        query = query.filter(Notification.action_required == action_required)
    if date_from:
        query = query.filter(Notification.created_at >= date_from)
    if date_to:
        # inclusive end-of-day when a date-only value is supplied
        if date_to.time() == datetime.min.time():
            date_to = date_to + timedelta(days=1) - timedelta(seconds=1)
        query = query.filter(Notification.created_at <= date_to)

    return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


# ────────────────────────────────────────────────────────────────────────────
# STATIC routes (must be before /{notification_id})
# ────────────────────────────────────────────────────────────────────────────

@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False,  # noqa: E712
    ).count()
    return {"count": count}


@router.get("/summary", response_model=NotificationSummary)
def get_summary(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Lightweight aggregated counts for the current user."""
    base = db.query(Notification).filter(Notification.user_id == current_user.id)

    unread = base.filter(Notification.read == False).count()  # noqa: E712
    important = base.filter(Notification.important == True).count()  # noqa: E712
    action_required = base.filter(Notification.action_required == True).count()  # noqa: E712

    # pending workflow approvals assigned to this user
    try:
        from app.models.workflow import WorkflowApproval, WorkflowApprovalStatus
        pending_approvals = db.query(WorkflowApproval).filter(
            WorkflowApproval.approver_user_id == current_user.id,
            WorkflowApproval.status == WorkflowApprovalStatus.PENDING,
        ).count()
    except Exception:
        pending_approvals = 0

    # failed jobs in user's orgs
    try:
        from app.models.job import Job
        org_ids = get_user_org_ids(db, current_user.id)
        failed_jobs = db.query(Job).filter(
            Job.status == "FAILED",
            Job.organization_id.in_(org_ids),
        ).count()
    except Exception:
        failed_jobs = 0

    return NotificationSummary(
        unread=unread,
        important=important,
        action_required=action_required,
        pending_approvals=pending_approvals,
        failed_jobs=failed_jobs,
    )


@router.get("/action-center", response_model=List[ActionItemResponse])
def get_action_center(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Aggregate action-required items across all relevant systems for the current user."""
    items: List[ActionItemResponse] = []
    org_ids = get_user_org_ids(db, current_user.id)

    # 1. Pending workflow approvals assigned to this user
    try:
        from app.models.workflow import WorkflowApproval, WorkflowApprovalStatus
        approvals = db.query(WorkflowApproval).filter(
            WorkflowApproval.approver_user_id == current_user.id,
            WorkflowApproval.status == WorkflowApprovalStatus.PENDING,
        ).order_by(WorkflowApproval.requested_at.desc()).limit(20).all()
        for a in approvals:
            items.append(ActionItemResponse(
                id=str(a.id),
                type="WORKFLOW_APPROVAL",
                title="Workflow Approval Required",
                description=f"Pending workflow approval assigned to you (entity: {a.entity_id})",
                entity_type="WORKFLOW_APPROVAL",
                entity_id=str(a.id),
                priority="HIGH",
                created_at=a.requested_at if a.requested_at.tzinfo else a.requested_at.replace(tzinfo=timezone.utc),
                action_url=f"/workflows",
            ))
    except Exception:
        pass

    # 2. Pending release approvals in user's orgs
    try:
        from app.models.delivery import ReleaseApproval, ReleaseApprovalStatus
        rel_approvals = db.query(ReleaseApproval).filter(
            ReleaseApproval.organization_id.in_(org_ids),
            ReleaseApproval.status == ReleaseApprovalStatus.PENDING,
        ).order_by(ReleaseApproval.created_at.desc()).limit(20).all()
        for ra in rel_approvals:
            items.append(ActionItemResponse(
                id=str(ra.id),
                type="RELEASE_APPROVAL",
                title="Release Approval Required",
                description=f"Release approval pending review",
                entity_type="RELEASE_APPROVAL",
                entity_id=str(ra.id),
                priority="HIGH",
                created_at=ra.created_at if ra.created_at.tzinfo else ra.created_at.replace(tzinfo=timezone.utc),
                action_url=f"/releases/operations",
            ))
    except Exception:
        pass

    # 3. Failed jobs in user's orgs (last 20)
    if org_ids:
        try:
            from app.models.job import Job
            failed_jobs = db.query(Job).filter(
                Job.status == "FAILED",
                Job.organization_id.in_(org_ids),
            ).order_by(Job.failed_at.desc()).limit(20).all()
            for j in failed_jobs:
                created = j.failed_at or j.created_at
                if created and not created.tzinfo:
                    created = created.replace(tzinfo=timezone.utc)
                items.append(ActionItemResponse(
                    id=str(j.id),
                    type="JOB_FAILURE",
                    title="Job Failed",
                    description=f"Job '{j.job_type}' failed after {j.attempts} attempt(s): {j.error_message or 'unknown error'}",
                    entity_type="JOB",
                    entity_id=str(j.id),
                    priority="HIGH",
                    created_at=created or datetime.now(timezone.utc),
                    action_url="/jobs",
                ))
        except Exception:
            pass

    # 4. Failed deployments in user's orgs (last 20)
    if org_ids:
        try:
            from app.models.delivery import Deployment, DeploymentStatus
            failed_deps = db.query(Deployment).filter(
                Deployment.status == DeploymentStatus.FAILED,
                Deployment.organization_id.in_(org_ids),
            ).order_by(Deployment.created_at.desc()).limit(20).all()
            for dep in failed_deps:
                created = dep.created_at
                if created and not created.tzinfo:
                    created = created.replace(tzinfo=timezone.utc)
                items.append(ActionItemResponse(
                    id=str(dep.id),
                    type="DEPLOYMENT_FAILURE",
                    title="Deployment Failed",
                    description=f"Deployment {_deployment_label(dep)} failed: {dep.error_message or 'unknown error'}",
                    entity_type="DEPLOYMENT",
                    entity_id=str(dep.id),
                    priority="HIGH",
                    created_at=created or datetime.now(timezone.utc),
                    action_url=f"/infrastructure/deployments/{dep.id}",
                ))
        except Exception:
            pass

    # 5. Daily reports with blockers (last 7 days, in user's orgs)
    if org_ids:
        try:
            from app.models.daily_report import DailyReport
            week_ago = datetime.now(timezone.utc).date() - timedelta(days=7)
            reports_with_blockers = db.query(DailyReport).filter(
                DailyReport.organization_id.in_(org_ids),
                DailyReport.report_date >= week_ago,
            ).order_by(DailyReport.created_at.desc()).limit(50).all()
            for r in reports_with_blockers:
                if r.blockers and len(r.blockers) > 0:
                    created = r.created_at
                    if created and not created.tzinfo:
                        created = created.replace(tzinfo=timezone.utc)
                    items.append(ActionItemResponse(
                        id=str(r.id),
                        type="DAILY_REPORT_BLOCKER",
                        title="Daily Report Blocker",
                        description=f"Report on {r.report_date} has {len(r.blockers)} blocker(s).",
                        entity_type="DAILY_REPORT",
                        entity_id=str(r.id),
                        priority="HIGH",
                        created_at=created or datetime.now(timezone.utc),
                        action_url="/daily-reports/blockers",
                    ))
        except Exception:
            pass

    # 6. Action-required notifications for this user
    action_notifs = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.action_required == True,  # noqa: E712
        Notification.read == False,  # noqa: E712
    ).order_by(Notification.created_at.desc()).limit(20).all()
    for n in action_notifs:
        items.append(ActionItemResponse(
            id=str(n.id),
            type="NOTIFICATION",
            title=n.title,
            description=n.message,
            entity_type=n.entity_type or "NOTIFICATION",
            entity_id=str(n.entity_id) if n.entity_id else None,
            priority=n.priority,
            created_at=n.created_at if n.created_at.tzinfo else n.created_at.replace(tzinfo=timezone.utc),
            action_url=None,
        ))

    # Sort all items by priority then created_at desc
    priority_order = {"URGENT": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}
    items.sort(key=lambda x: (priority_order.get(x.priority, 2), -x.created_at.timestamp()))
    return items


@router.patch("/read-all")
@router.post("/read-all")
def mark_all_read(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False,  # noqa: E712
    ).update({"read": True, "read_at": datetime.now(timezone.utc)})
    db.commit()
    _broadcast("notification.read_all", None, current_user.id)
    return {"message": "All marked as read"}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_prefs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return get_preferences(db, current_user.id)


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
def update_prefs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    request: NotificationPreferenceBase,
) -> Any:
    pref = get_preferences(db, current_user.id)
    for k, v in request.dict().items():
        if hasattr(pref, k):
            setattr(pref, k, v)
    db.commit()
    db.refresh(pref)
    return pref


# ────────────────────────────────────────────────────────────────────────────
# DYNAMIC /{notification_id} routes (must come after static routes)
# ────────────────────────────────────────────────────────────────────────────

@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    notification_id: UUID,
) -> Any:
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    return n


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    notification_id: UUID,
) -> Any:
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = True
    n.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(n)
    _broadcast("notification.read", n.id, current_user.id, read=True)
    return n


@router.patch("/{notification_id}/unread", response_model=NotificationResponse)
def mark_unread(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    notification_id: UUID,
) -> Any:
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = False
    n.read_at = None
    db.commit()
    db.refresh(n)
    _broadcast("notification.updated", n.id, current_user.id, read=False)
    return n


@router.patch("/{notification_id}/important", response_model=NotificationResponse)
def mark_important(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    notification_id: UUID,
) -> Any:
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.important = True
    db.commit()
    db.refresh(n)
    _broadcast("notification.updated", n.id, current_user.id, important=True)
    return n


@router.patch("/{notification_id}/unimportant", response_model=NotificationResponse)
def mark_unimportant(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    notification_id: UUID,
) -> Any:
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.important = False
    db.commit()
    db.refresh(n)
    _broadcast("notification.updated", n.id, current_user.id, important=False)
    return n


@router.delete("/{notification_id}")
def delete_notification(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    notification_id: UUID,
) -> Any:
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(n)
    db.commit()
    _broadcast("notification.deleted", notification_id, current_user.id)
    return {"message": "Deleted"}
