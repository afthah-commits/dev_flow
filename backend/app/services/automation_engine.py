import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.automation import Automation, AutomationExecution, AutomationActionExecution
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.audit import AuditEvent
from app.models.collaboration import Comment, Discussion
from app.core.security import get_password_hash
import json

def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    keys = path.split('.')
    val = data
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            return None
    return val

def evaluate_condition(condition: Dict[str, Any], event_payload: Dict[str, Any]) -> bool:
    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")

    actual_value = get_nested_value(event_payload, field) if field else None

    if operator == "EQUALS":
        return actual_value == value
    elif operator == "NOT_EQUALS":
        return actual_value != value
    elif operator == "CONTAINS":
        return value in actual_value if actual_value and isinstance(actual_value, (str, list)) else False
    elif operator == "NOT_CONTAINS":
        return value not in actual_value if actual_value and isinstance(actual_value, (str, list)) else True
    elif operator == "IS_EMPTY":
        return not actual_value
    elif operator == "IS_NOT_EMPTY":
        return bool(actual_value)
    
    # numeric comparisons
    try:
        if operator == "GREATER_THAN":
            return float(actual_value) > float(value)
        elif operator == "LESS_THAN":
            return float(actual_value) < float(value)
        elif operator == "GREATER_OR_EQUAL":
            return float(actual_value) >= float(value)
        elif operator == "LESS_OR_EQUAL":
            return float(actual_value) <= float(value)
    except (ValueError, TypeError):
        return False
        
    if operator == "IN":
        return actual_value in value if isinstance(value, list) else False
    elif operator == "NOT_IN":
        return actual_value not in value if isinstance(value, list) else True

    return False

def evaluate_condition_group(group: Dict[str, Any], event_payload: Dict[str, Any]) -> bool:
    if not group:
        return True
    
    op = group.get("logical_operator", "ALL")  # ALL, ANY, NOT
    conditions = group.get("conditions", [])

    if op == "ALL":
        return all(evaluate_condition(c, event_payload) if "operator" in c else evaluate_condition_group(c, event_payload) for c in conditions)
    elif op == "ANY":
        return any(evaluate_condition(c, event_payload) if "operator" in c else evaluate_condition_group(c, event_payload) for c in conditions)
    elif op == "NOT":
        if not conditions:
            return True
        return not (evaluate_condition(conditions[0], event_payload) if "operator" in conditions[0] else evaluate_condition_group(conditions[0], event_payload))
    
    return True

async def execute_action(db: Session, action: Dict[str, Any], execution: AutomationExecution, event_payload: Dict[str, Any]) -> AutomationActionExecution:
    action_type = action.get("type")
    
    action_exec = AutomationActionExecution(
        execution_id=execution.id,
        action_type=action_type,
        status="RUNNING",
        input_data=action,
        started_at=datetime.now(timezone.utc)
    )
    db.add(action_exec)
    db.commit()

    try:
        # Resolve target organization
        org_id = execution.organization_id
        
        # MOCK IMPLEMENTATION OF ACTIONS - reuse existing logic where applicable
        if action_type == "CREATE_TASK":
            title = action.get("title", "Automated Task")
            # In a real impl, we would use Task CRUD, here we just insert directly or call crud.task
            new_task = Task(
                organization_id=org_id,
                project_id=action.get("project_id") or event_payload.get("project_id"),
                title=title,
                status=action.get("status", "TODO"),
                priority=action.get("priority", "MEDIUM")
            )
            db.add(new_task)
            db.flush()
            action_exec.output_data = {"task_id": new_task.id}
            
        elif action_type == "UPDATE_TASK":
            task_id = action.get("task_id") or event_payload.get("task_id")
            if task_id:
                task = db.query(Task).filter(Task.id == task_id, Task.organization_id == org_id).first()
                if task:
                    if "status" in action: task.status = action["status"]
                    if "priority" in action: task.priority = action["priority"]
                    action_exec.output_data = {"task_id": task.id, "updated": True}
                    
        elif action_type == "CREATE_COMMENT":
            entity_id = action.get("entity_id") or event_payload.get("task_id") or event_payload.get("entity_id")
            if entity_id:
                comment = Comment(
                    organization_id=org_id,
                    entity_type=action.get("entity_type", "TASK"),
                    entity_id=entity_id,
                    content=action.get("content", "Automated comment")
                )
                db.add(comment)
                db.flush()
                action_exec.output_data = {"comment_id": str(comment.id)}
        
        elif action_type == "CREATE_AUDIT_EVENT":
            audit = AuditEvent(
                organization_id=org_id,
                action=action.get("audit_action", "AUTOMATION_CUSTOM_EVENT"),
                entity_type=action.get("entity_type", "AUTOMATION"),
                entity_id=execution.automation_id,
                details=action.get("details", {})
            )
            db.add(audit)
            db.flush()
            action_exec.output_data = {"audit_id": audit.id}

        # More actions here...

        action_exec.status = "SUCCESS"
        
    except Exception as e:
        action_exec.status = "FAILED"
        action_exec.error_message = str(e)
        
    action_exec.completed_at = datetime.now(timezone.utc)
    db.commit()
    return action_exec

async def handle_event(db: Session, event_payload: Dict[str, Any]):
    org_id = event_payload.get("organization_id")
    event_type = event_payload.get("event_type")
    
    if not org_id or not event_type:
        return

    automations = db.query(Automation).filter(
        Automation.organization_id == org_id,
        Automation.enabled == True,
        Automation.trigger_type == event_type
    ).all()

    for automation in automations:
        # Check conditions
        if not evaluate_condition_group(automation.conditions, event_payload):
            continue

        idempotency_key = f"{automation.id}_{event_payload.get('entity_id', '')}_{event_payload.get('timestamp', '')}"
        
        existing = db.query(AutomationExecution).filter(AutomationExecution.idempotency_key == idempotency_key).first()
        if existing:
            continue
            
        execution = AutomationExecution(
            automation_id=automation.id,
            organization_id=org_id,
            trigger_event=event_type,
            status="RUNNING",
            execution_context=event_payload,
            idempotency_key=idempotency_key
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        success = True
        for action in automation.actions:
            res = await execute_action(db, action, execution, event_payload)
            if res.status == "FAILED":
                success = False
                break
                
        execution.status = "SUCCESS" if success else "FAILED"
        execution.completed_at = datetime.now(timezone.utc)
        start = execution.started_at.replace(tzinfo=timezone.utc) if execution.started_at.tzinfo is None else execution.started_at
        execution.duration_ms = int((execution.completed_at - start).total_seconds() * 1000)
        db.commit()

