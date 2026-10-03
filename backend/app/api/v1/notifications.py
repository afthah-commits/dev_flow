from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Any, List
from datetime import datetime, timezone

from app.api import deps
from app.models.user import User
from app.models.notification import Notification, NotificationPreference
from app.schemas.notification import NotificationResponse, NotificationPreferenceBase, NotificationPreferenceResponse, UnreadCountResponse
from app.services.notification_service import get_preferences, check_and_generate_overdue_notifications, check_and_generate_health_notifications

router = APIRouter()

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    # Trigger generation lazily
    check_and_generate_overdue_notifications(db, current_user.id)
    check_and_generate_health_notifications(db, current_user.id)
    
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(50).all()

@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    count = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.read == False).count()
    return {"count": count}

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    notification_id: UUID
) -> Any:
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if n:
        n.read = True
        n.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(n)
    return n

@router.patch("/read-all")
def mark_all_read(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.read == False).update(
        {"read": True, "read_at": datetime.now(timezone.utc)}
    )
    db.commit()
    return {"message": "All marked as read"}

@router.delete("/{notification_id}")
def delete_notification(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    notification_id: UUID
) -> Any:
    db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Deleted"}

@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_prefs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return get_preferences(db, current_user.id)

@router.patch("/preferences", response_model=NotificationPreferenceResponse)
def update_prefs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    request: NotificationPreferenceBase
) -> Any:
    pref = get_preferences(db, current_user.id)
    pref.task_notifications = request.task_notifications
    pref.deadline_notifications = request.deadline_notifications
    pref.project_health_notifications = request.project_health_notifications
    pref.github_notifications = request.github_notifications
    pref.ai_notifications = request.ai_notifications
    db.commit()
    db.refresh(pref)
    return pref
