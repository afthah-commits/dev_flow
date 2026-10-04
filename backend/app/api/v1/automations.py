import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.automation import Automation, AutomationExecution, AutomationActionExecution
from app.schemas.automation import AutomationCreate, AutomationUpdate, AutomationResponse, AutomationExecutionResponse
from app.services.automation_engine import handle_event

router = APIRouter()

@router.get("", response_model=List[AutomationResponse])
def list_automations(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: str = None
) -> Any:
    # In real app verify RBAC. Assuming viewer logic holds for org_id.
    if not organization_id:
        raise HTTPException(status_code=400, detail="organization_id is required")
        
    automations = db.query(Automation).filter(Automation.organization_id == organization_id).all()
    return automations

@router.post("", response_model=AutomationResponse)
def create_automation(
    *,
    db: Session = Depends(deps.get_db),
    automation_in: AutomationCreate,
    organization_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    automation = Automation(
        organization_id=organization_id,
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
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    return automation

@router.patch("/{automation_id}", response_model=AutomationResponse)
def update_automation(
    automation_id: str,
    automation_in: AutomationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
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
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    db.delete(automation)
    db.commit()
    return {"ok": True}

@router.get("/{automation_id}/executions", response_model=List[AutomationExecutionResponse])
def get_executions(
    automation_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    executions = db.query(AutomationExecution).filter(AutomationExecution.automation_id == automation_id).all()
    # Eager load actions if needed, for simplicity we just return base for now
    return executions

@router.post("/{automation_id}/test")
async def test_automation(
    automation_id: str,
    payload: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
        
    from app.services.automation_engine import evaluate_condition_group
    passed = evaluate_condition_group(automation.conditions, payload)
    
    return {
        "conditions_passed": passed,
        "planned_actions": automation.actions,
        "message": "Dry run successful"
    }
