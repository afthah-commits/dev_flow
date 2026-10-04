import uuid
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import get_history
import json
from uuid import UUID

from app.core.context import get_current_user_id, get_current_org_id
from app.models.audit import AuditEvent
from app.services.audit_service import sanitize_metadata
from app.services.notification_service import create_notification
from app.models.notification import NotificationType

# Entity mapping
def get_entity_name(obj):
    return obj.__class__.__name__

def get_entity_info(obj):
    # try to get project_id
    project_id = getattr(obj, "project_id", None)
    if not project_id and get_entity_name(obj) == "Project":
        project_id = obj.id
    
    # try to get team_id
    team_id = getattr(obj, "team_id", None)
    if not team_id and get_entity_name(obj) == "Team":
        team_id = obj.id
        
    return {
        "entity_type": get_entity_name(obj).upper(),
        "entity_id": getattr(obj, "id", None),
        "project_id": project_id,
        "team_id": team_id
    }

def setup_audit_listeners(engine):
    from sqlalchemy.orm import sessionmaker
    @event.listens_for(Session, "before_commit")
    def before_commit(session: Session):
        org_id = get_current_org_id()
        if not org_id:
            # We can't log without org_id if not in a request context, 
            # except we might try to extract it from the objects if available.
            pass
            
        user_id = get_current_user_id()
        
        events_to_add = []
        notifications_to_add = []
        
        # New objects
        for obj in session.new:
            name = get_entity_name(obj)
            if name in ["AuditEvent", "Notification", "NotificationPreference"]:
                continue
            
            info = get_entity_info(obj)
            e_org_id = getattr(obj, "organization_id", org_id)
            if isinstance(e_org_id, str): e_org_id = uuid.UUID(e_org_id)
            if not e_org_id: continue
            
            metadata = {}
            if hasattr(obj, "__dict__"):
                metadata = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
                
            events_to_add.append(AuditEvent(
                organization_id=e_org_id,
                actor_user_id=user_id,
                event_type=f"{name.upper()}_CREATED",
                entity_type=info["entity_type"],
                entity_id=uuid.UUID(str(info["entity_id"])) if isinstance(info["entity_id"], str) else info["entity_id"],
                project_id=info["project_id"],
                team_id=info["team_id"],
                metadata_=sanitize_metadata(metadata)
            ))
            
            # Basic notifications
            if name == "Task" and getattr(obj, "assignee_id", None):
                notifications_to_add.append({
                    "user_id": obj.assignee_id,
                    "n_type": "TASK_ASSIGNED",
                    "title": "Task Assigned",
                    "message": f"You were assigned to task {getattr(obj, 'title', '')}",
                    "project_id": info["project_id"],
                    "priority": "NORMAL",
                    "entity_type": "TASK",
                    "entity_id": info["entity_id"]
                })

        # Updated objects
        for obj in session.dirty:
            name = get_entity_name(obj)
            if name in ["AuditEvent", "Notification", "NotificationPreference", "User"]:
                continue
                
            info = get_entity_info(obj)
            e_org_id = getattr(obj, "organization_id", org_id)
            if isinstance(e_org_id, str): e_org_id = uuid.UUID(e_org_id)
            if not e_org_id: continue
            
            changes = []
            for col in obj.__mapper__.columns:
                hist = get_history(obj, col.name)
                if hist.has_changes():
                    old_val = hist.deleted[0] if hist.deleted else None
                    new_val = hist.added[0] if hist.added else None
                    if old_val != new_val:
                        changes.append({
                            "field": col.name,
                            "old": old_val,
                            "new": new_val
                        })
                        
                        # Handle specific task changes
                        if name == "Task" and col.name == "assignee_id" and new_val:
                            notifications_to_add.append({
                                "user_id": new_val,
                                "n_type": "TASK_ASSIGNED",
                                "title": "Task Assigned",
                                "message": f"You were assigned to task {getattr(obj, 'title', '')}",
                                "project_id": info["project_id"],
                                "priority": "NORMAL",
                                "entity_type": "TASK",
                                "entity_id": info["entity_id"]
                            })
                        if name == "Task" and col.name == "status":
                            notifications_to_add.append({
                                "user_id": getattr(obj, "assignee_id", None),
                                "n_type": "TASK_STATUS_CHANGED",
                                "title": "Task Status Updated",
                                "message": f"Task {getattr(obj, 'title', '')} is now {new_val}",
                                "project_id": info["project_id"],
                                "priority": "LOW",
                                "entity_type": "TASK",
                                "entity_id": info["entity_id"]
                            })

            if changes:
                events_to_add.append(AuditEvent(
                    organization_id=e_org_id,
                    actor_user_id=user_id,
                    event_type=f"{name.upper()}_UPDATED",
                    entity_type=info["entity_type"],
                    entity_id=uuid.UUID(str(info["entity_id"])) if isinstance(info["entity_id"], str) else info["entity_id"],
                    project_id=info["project_id"],
                    team_id=info["team_id"],
                    metadata_=sanitize_metadata({"changes": changes})
                ))

        # Deleted objects
        for obj in session.deleted:
            name = get_entity_name(obj)
            if name in ["AuditEvent", "Notification", "NotificationPreference"]:
                continue
                
            info = get_entity_info(obj)
            e_org_id = getattr(obj, "organization_id", org_id)
            if isinstance(e_org_id, str): e_org_id = uuid.UUID(e_org_id)
            if not e_org_id: continue
            
            events_to_add.append(AuditEvent(
                organization_id=e_org_id,
                actor_user_id=user_id,
                event_type=f"{name.upper()}_DELETED",
                entity_type=info["entity_type"],
                entity_id=uuid.UUID(str(info["entity_id"])) if isinstance(info["entity_id"], str) else info["entity_id"],
                project_id=info["project_id"],
                team_id=info["team_id"],
                metadata_=sanitize_metadata({"id": str(info["entity_id"])})
            ))
            
        if events_to_add:
            session.add_all(events_to_add)
            
        # We can't generate notifications safely here without possibly conflicting, 
        # but session before_commit is safe for adding more objects!
        for n in notifications_to_add:
            if n["user_id"]: # Only notify if there's a target user
                session.add(Notification(
                    user_id=n["user_id"],
                    project_id=n["project_id"],
                    type=n["n_type"],
                    title=n["title"],
                    message=n["message"],
                    priority=n["priority"],
                    entity_type=n["entity_type"],
                    entity_id=n["entity_id"]
                ))
