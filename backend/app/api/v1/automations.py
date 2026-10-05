import uuid
from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.automation import Automation, AutomationExecution, AutomationActionExecution
from app.schemas.automation import AutomationCreate, AutomationUpdate, AutomationResponse, AutomationExecutionResponse
from app.services.automation_engine import handle_event

router = APIRouter()

def _require_org_access(db: Session, current_user: User, organization_id: str) -> UUID:
    """Validate the caller is a member of the target organization.

    Phase 31: previously these endpoints trusted the organization_id query
    parameter (or the bare automation id) with no membership check, allowing
    cross-tenant reads and writes.
    """
    try:
        org_uuid = UUID(str(organization_id))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=404, detail="Automation not found")
    deps.require_organization_member(db, current_user.id, org_uuid)
    return org_uuid

def _require_automation_access(db: Session, current_user: User, automation_id: str) -> Automation:
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    _require_org_access(db, current_user, automation.organization_id)
    return automation

@router.get("", response_model=List[AutomationResponse])
def list_automations(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: str = None
) -> Any:
    if not organization_id:
        raise HTTPException(status_code=400, detail="organization_id is required")
    org_uuid = _require_org_access(db, current_user, organization_id)

    # Automation.organization_id is a String column; compare against its text form.
    automations = db.query(Automation).filter(Automation.organization_id == str(org_uuid)).all()
    return automations

@router.post("", response_model=AutomationResponse)
def create_automation(
    *,
    db: Session = Depends(deps.get_db),
    automation_in: AutomationCreate,
    organization_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    org_uuid = _require_org_access(db, current_user, organization_id)
    automation = Automation(
        organization_id=str(org_uuid),
        created_by=str(current_user.id),
        name=automation_in.name,
        description=automation_in.description,
        enabled=automation_in.enabled,
        trigger_type=automation_in.trigger_type,
        configuration=automation_in.configuration,
        conditions=automation_in.conditions,
        actions=automation_in.actions,
        execution_mode=automation_in.execution_mode
    )
    db.add(automation)
    db.commit()
    db.refresh(automation)
    return automation

@router.get("/{automation_id}", response_model=AutomationResponse)
def get_automation(
    automation_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return _require_automation_access(db, current_user, automation_id)

@router.patch("/{automation_id}", response_model=AutomationResponse)
def update_automation(
    automation_id: str,
    automation_in: AutomationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    automation = _require_automation_access(db, current_user, automation_id)

    update_data = automation_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(automation, field, value)
        
    db.commit()
    db.refresh(automation)
    return automation

@router.delete("/{automation_id}")
def delete_automation(
    automation_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    automation = _require_automation_access(db, current_user, automation_id)
    db.delete(automation)
    db.commit()
    return {"ok": True}

@router.get("/{automation_id}/executions", response_model=List[AutomationExecutionResponse])
def get_executions(
    automation_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    automation = _require_automation_access(db, current_user, automation_id)
    executions = db.query(AutomationExecution).filter(AutomationExecution.automation_id == automation.id).all()
    # Eager load actions if needed, for simplicity we just return base for now
    return executions

@router.post("/{automation_id}/test")
async def test_automation(
    automation_id: str,
    payload: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    automation = _require_automation_access(db, current_user, automation_id)
        
    from app.services.automation_engine import evaluate_condition_group
    passed = evaluate_condition_group(automation.conditions, payload)
    
    return {
        "conditions_passed": passed,
        "planned_actions": automation.actions,
        "message": "Dry run successful"
    }
