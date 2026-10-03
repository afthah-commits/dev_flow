from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationPreference, NotificationType
from app.models.task import Task
from app.models.project import Project
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

def create_notification(db: Session, user_id: UUID, n_type: str, title: str, message: str, project_id: UUID = None):
    # Deduplication
    recent = datetime.now(timezone.utc) - timedelta(hours=24)
    exists = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.type == n_type,
        Notification.title == title,
        Notification.created_at > recent
    ).first()
    
    if exists:
        return
        
    n = Notification(user_id=user_id, project_id=project_id, type=n_type, title=title, message=message)
    db.add(n)
    db.commit()

def check_and_generate_overdue_notifications(db: Session, user_id: UUID):
    pref = get_preferences(db, user_id)
    if not pref.task_notifications:
        return
        
    now = datetime.now(timezone.utc)
    
    # Overdue tasks
    tasks = db.query(Task).join(Project).filter(Project.owner_id == user_id, Task.status != "DONE", Task.due_date != None).all()
    for t in tasks:
        if t.due_date.replace(tzinfo=timezone.utc) < now:
            create_notification(db, user_id, NotificationType.TASK_OVERDUE, f"Task Overdue", f"Task '{t.title}' is overdue.", t.project_id)
        elif t.due_date.replace(tzinfo=timezone.utc) < now + timedelta(days=2) and pref.deadline_notifications:
            create_notification(db, user_id, NotificationType.TASK_DUE_SOON, f"Task Due Soon", f"Task '{t.title}' is due soon.", t.project_id)

def check_and_generate_health_notifications(db: Session, user_id: UUID):
    pref = get_preferences(db, user_id)
    if not pref.project_health_notifications:
        return
        
    projects = db.query(Project).filter(Project.owner_id == user_id).all()
    for p in projects:
        health = calculate_project_health(db, p.id)
        if health["status"] == "At Risk":
            create_notification(db, user_id, NotificationType.PROJECT_AT_RISK, "Project At Risk", f"Project '{p.name}' is At Risk (Score: {health['score']}).", p.id)
