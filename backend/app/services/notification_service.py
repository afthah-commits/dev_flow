from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationPreference, NotificationType
from app.models.task import Task
from app.models.project import Project
from app.models.organization import OrganizationMember
from app.services.analytics_service import calculate_project_health
from uuid import UUID
from datetime import datetime, timezone, timedelta


def get_preferences(db: Session, user_id: UUID) -> NotificationPreference:
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
    if not pref:
        pref = NotificationPreference(user_id=user_id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def get_user_org_ids(db: Session, user_id: UUID) -> list:
    """Return list of organization UUIDs for the given user."""
    members = db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).all()
    return [m.organization_id for m in members]


def get_org_member_user_ids(db: Session, org_id: UUID) -> list:
    """Return list of user UUIDs that are members of the given org."""
    members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).all()
    return [m.user_id for m in members]


def create_notification(
    db: Session,
    user_id: UUID,
    n_type: str,
    title: str,
    message: str,
    project_id: UUID = None,
    priority: str = "NORMAL",
    entity_type: str = None,
    entity_id: UUID = None,
    organization_id: UUID = None,
    action_required: bool = False,
    important: bool = False,
):
    """Create a notification with built-in deduplication (24h window per user+type+entity)."""
    recent = datetime.now(timezone.utc) - timedelta(hours=24)

    query = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.type == n_type,
        Notification.created_at > recent
    )

    if entity_type and entity_id:
        query = query.filter(Notification.entity_type == entity_type, Notification.entity_id == entity_id)
    else:
        query = query.filter(Notification.title == title)

    exists = query.first()

    if exists:
        return None

    from app.services.channels import dispatcher

    notification_data = {
        "organization_id": organization_id,
        "project_id": project_id,
        "type": n_type,
        "title": title,
        "message": message,
        "priority": priority,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action_required": action_required,
        "important": important,
    }

    dispatcher.dispatch(db, user_id, notification_data)
    return True


def check_and_generate_overdue_notifications(db: Session, user_id: UUID):
    pref = get_preferences(db, user_id)
    if not pref.task_notifications:
        return

    now = datetime.now(timezone.utc)

    tasks = db.query(Task).join(Project).filter(
        Project.owner_id == user_id,
        Task.status != "DONE",
        Task.due_date != None
    ).all()
    for t in tasks:
        if t.due_date.replace(tzinfo=timezone.utc) < now:
            create_notification(
                db, user_id, NotificationType.TASK_OVERDUE,
                "Task Overdue", f"Task '{t.title}' is overdue.",
                t.project_id, priority="HIGH", entity_type="TASK", entity_id=t.id
            )
        elif t.due_date.replace(tzinfo=timezone.utc) < now + timedelta(days=2) and pref.deadline_notifications:
            create_notification(
                db, user_id, NotificationType.TASK_DUE_SOON,
                "Task Due Soon", f"Task '{t.title}' is due soon.",
                t.project_id, priority="NORMAL", entity_type="TASK", entity_id=t.id
            )


def check_and_generate_health_notifications(db: Session, user_id: UUID):
    pref = get_preferences(db, user_id)
    if not pref.project_health_notifications:
        return

    projects = db.query(Project).filter(Project.owner_id == user_id).all()
    for p in projects:
        health = calculate_project_health(db, p.id)
        if health["status"] == "At Risk":
            create_notification(
                db, user_id, NotificationType.PROJECT_AT_RISK,
                "Project At Risk", f"Project '{p.name}' is At Risk (Score: {health['score']}).",
                p.id, priority="HIGH", entity_type="PROJECT", entity_id=p.id
            )


# ─── Phase 36: domain event helpers ─────────────────────────────────────────

def notify_job_failure(db: Session, org_id: UUID, job_id: UUID, job_type: str, error_message: str = None):
    """Notify org members of a critical job failure (skips anyone who already
    has a notification for this job — the scheduler writes its own JOB_FAILED
    notice for owners/admins, so this never duplicates it)."""
    user_ids = get_org_member_user_ids(db, org_id)
    msg = f"Job '{job_type}' failed"
    if error_message:
        msg += f": {error_message[:120]}"

    already_notified = {
        row[0] for row in db.query(Notification.user_id).filter(
            Notification.entity_id == job_id,
            Notification.created_at > datetime.now(timezone.utc) - timedelta(hours=24),
        ).all()
    }

    for uid in user_ids:
        if uid in already_notified:
            continue
        pref = get_preferences(db, uid)
        if not pref.job_notifications:
            continue
        create_notification(
            db, uid, NotificationType.JOB_FAILURE,
            "Job Failed", msg,
            priority="HIGH",
            entity_type="JOB",
            entity_id=job_id,
            organization_id=org_id,
            action_required=True,
        )


def notify_deployment_failed(db: Session, org_id: UUID, deployment_id: UUID, deployment_name: str):
    """Notify all org members of a deployment failure."""
    user_ids = get_org_member_user_ids(db, org_id)
    for uid in user_ids:
        pref = get_preferences(db, uid)
        if not pref.deployment_notifications:
            continue
        create_notification(
            db, uid, NotificationType.DEPLOYMENT_FAILED,
            "Deployment Failed", f"Deployment '{deployment_name}' has failed.",
            priority="HIGH",
            entity_type="DEPLOYMENT",
            entity_id=deployment_id,
            organization_id=org_id,
            action_required=True,
        )


def notify_deployment_event(db: Session, org_id: UUID, deployment_id: UUID, deployment_name: str, event: str):
    """Notify all org members of a deployment event (started/success/rollback)."""
    type_map = {
        "started": (NotificationType.DEPLOYMENT_STARTED, "NORMAL", False),
        "success": (NotificationType.DEPLOYMENT_SUCCESS, "NORMAL", False),
        "rollback": (NotificationType.DEPLOYMENT_ROLLBACK, "HIGH", True),
    }
    if event not in type_map:
        return
    n_type, priority, action_req = type_map[event]
    user_ids = get_org_member_user_ids(db, org_id)
    for uid in user_ids:
        pref = get_preferences(db, uid)
        if not pref.deployment_notifications:
            continue
        create_notification(
            db, uid, n_type,
            f"Deployment {event.title()}", f"Deployment '{deployment_name}' {event}.",
            priority=priority,
            entity_type="DEPLOYMENT",
            entity_id=deployment_id,
            organization_id=org_id,
            action_required=action_req,
        )


def notify_workflow_approval_requested(
    db: Session,
    approver_user_id: UUID,
    org_id: UUID,
    approval_id: UUID,
    entity_info: str,
):
    """Notify approver of a pending workflow approval."""
    pref = get_preferences(db, approver_user_id)
    if not pref.workflow_approval_notifications:
        return
    create_notification(
        db, approver_user_id, NotificationType.WORKFLOW_APPROVAL_REQUESTED,
        "Workflow Approval Required", f"Your approval is required for: {entity_info}",
        priority="HIGH",
        entity_type="WORKFLOW_APPROVAL",
        entity_id=approval_id,
        organization_id=org_id,
        action_required=True,
        important=True,
    )


def notify_release_approval_requested(
    db: Session,
    approver_user_id: UUID,
    org_id: UUID,
    release_approval_id: UUID,
    release_name: str,
):
    """Notify approver of a pending release approval."""
    pref = get_preferences(db, approver_user_id)
    if not pref.release_notifications:
        return
    create_notification(
        db, approver_user_id, NotificationType.RELEASE_APPROVAL_REQUESTED,
        "Release Approval Required", f"Your approval is required for release: {release_name}",
        priority="HIGH",
        entity_type="RELEASE_APPROVAL",
        entity_id=release_approval_id,
        organization_id=org_id,
        action_required=True,
        important=True,
    )


def notify_daily_report_blocker(db: Session, org_id: UUID, report_id: UUID, author_name: str, blockers: list):
    """Notify org members when a daily report is submitted with blockers."""
    if not blockers:
        return
    count = len(blockers)
    user_ids = get_org_member_user_ids(db, org_id)
    for uid in user_ids:
        pref = get_preferences(db, uid)
        if not pref.daily_report_notifications:
            continue
        create_notification(
            db, uid, NotificationType.DAILY_REPORT_BLOCKER,
            "Daily Report Blocker",
            f"{author_name} reported {count} blocker(s) in their daily report.",
            priority="HIGH",
            entity_type="DAILY_REPORT",
            entity_id=report_id,
            organization_id=org_id,
            action_required=True,
        )


def notify_release_decision(
    db: Session,
    requester_user_id: UUID,
    org_id: UUID,
    release_id: UUID,
    release_name: str,
    decision: str,
    reviewer_name: str,
):
    """Notify the requester that their release approval was approved/rejected."""
    if not requester_user_id:
        return
    pref = get_preferences(db, requester_user_id)
    if not pref.release_notifications:
        return
    approved = decision == "approved"
    create_notification(
        db, requester_user_id,
        NotificationType.RELEASE_APPROVED if approved else NotificationType.RELEASE_REJECTED,
        f"Release {decision.title()}",
        f"{reviewer_name} {decision} release: {release_name}",
        priority="HIGH" if not approved else "NORMAL",
        entity_type="RELEASE",
        entity_id=release_id,
        organization_id=org_id,
        action_required=not approved,
        important=not approved,
    )


def notify_release_event(
    db: Session,
    org_id: UUID,
    release_id: UUID,
    release_name: str,
    event: str,
    target_env: str = None,
):
    """Notify org members of a release lifecycle event (promoted/rollback)."""
    type_map = {
        "promoted": (NotificationType.RELEASE_PROMOTED, "NORMAL", False),
        "rollback": (NotificationType.RELEASE_ROLLBACK, "URGENT", True),
    }
    if event not in type_map:
        return
    n_type, priority, action_req = type_map[event]
    suffix = f" to {target_env}" if target_env else ""
    user_ids = get_org_member_user_ids(db, org_id)
    for uid in user_ids:
        pref = get_preferences(db, uid)
        if not pref.release_notifications:
            continue
        create_notification(
            db, uid, n_type,
            f"Release {event.title()}",
            f"Release '{release_name}' was {event}{suffix}.",
            priority=priority,
            entity_type="RELEASE",
            entity_id=release_id,
            organization_id=org_id,
            action_required=action_req,
            important=event == "rollback",
        )


def notify_automation_failure(
    db: Session,
    org_id,
    automation_id,
    automation_name: str,
    error_message: str = None,
):
    """Notify org members when an automation execution fails."""
    msg = f"Automation '{automation_name}' failed"
    if error_message:
        msg += f": {error_message[:120]}"
    # Automation ids/org ids are String-typed in this schema; normalize to UUID
    # so member lookups and the notification's UUID FK still line up.
    try:
        org_id = UUID(str(org_id))
    except Exception:
        return
    try:
        automation_id = UUID(str(automation_id))
    except Exception:
        automation_id = None
    user_ids = get_org_member_user_ids(db, org_id)
    for uid in user_ids:
        pref = get_preferences(db, uid)
        if not pref.automation_notifications:
            continue
        create_notification(
            db, uid, NotificationType.AUTOMATION_FAILURE,
            "Automation Failed", msg,
            priority="HIGH",
            entity_type="AUTOMATION",
            entity_id=automation_id,
            organization_id=org_id,
            action_required=True,
        )


def notify_client_request(
    db: Session,
    org_id: UUID,
    request_id: UUID,
    title: str,
    event: str,
    actor_name: str,
):
    """Notify org members about client request activity (created/updated)."""
    created = event == "created"
    n_type = NotificationType.CLIENT_REQUEST_CREATED if created else NotificationType.CLIENT_REQUEST_UPDATED
    user_ids = get_org_member_user_ids(db, org_id)
    for uid in user_ids:
        pref = get_preferences(db, uid)
        if not pref.client_request_notifications:
            continue
        create_notification(
            db, uid, n_type,
            "Client Request" if created else "Client Request Updated",
            f"{actor_name} {event} client request: {title}",
            priority="HIGH" if created else "NORMAL",
            entity_type="CLIENT_REQUEST",
            entity_id=request_id,
            organization_id=org_id,
            action_required=created,
        )


def notify_team_activity(
    db: Session,
    org_id: UUID,
    recipient_id: UUID,
    title: str,
    message: str,
    entity_type: str,
    entity_id: UUID,
    project_id: UUID = None,
):
    """Notify a single recipient about a team activity (e.g. task assignment)."""
    pref = get_preferences(db, recipient_id)
    if not pref.team_activity_notifications:
        return
    create_notification(
        db, recipient_id, NotificationType.TEAM_ACTIVITY,
        title, message,
        project_id=project_id,
        priority="NORMAL",
        entity_type=entity_type,
        entity_id=entity_id,
        organization_id=org_id,
    )


def check_and_generate_daily_report_reminder(db: Session, user_id: UUID):
    """Lazily remind a user who has reported before but has no report for today.

    Deterministic: only fires for users with at least one DailyReport in the last
    30 days, so non-reporting users are never spammed. The 24h dedup window in
    create_notification means at most one reminder per day per user.
    """
    pref = get_preferences(db, user_id)
    if not pref.daily_report_notifications:
        return

    today = datetime.now(timezone.utc).date()
    from app.models.daily_report import DailyReport

    has_history = db.query(DailyReport.id).filter(
        DailyReport.author_user_id == user_id,
        DailyReport.report_date >= today - timedelta(days=30),
    ).first()
    if not has_history:
        return

    has_today = db.query(DailyReport.id).filter(
        DailyReport.author_user_id == user_id,
        DailyReport.report_date == today,
    ).first()
    if has_today:
        return

    org_row = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id
    ).first()
    create_notification(
        db, user_id, NotificationType.DAILY_REPORT_REMINDER,
        "Daily Report Reminder",
        f"You have not submitted a daily report for {today.isoformat()} yet.",
        priority="NORMAL",
        entity_type="DAILY_REPORT",
        organization_id=org_row.organization_id if org_row else None,
        action_required=True,
    )
