from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.task import Label
from app.schemas.label import LabelCreate, LabelUpdate, LabelResponse

router = APIRouter()

@router.post("", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
def create_label(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    label_in: LabelCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    # Could restrict to admin/owner here
    existing = db.query(Label).filter(Label.organization_id == org_id, Label.name == label_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Label already exists in this organization")
        
    label = Label(**label_in.model_dump(), organization_id=org_id)
    db.add(label)
    db.commit()
    db.refresh(label)
    return label

@router.get("", response_model=List[LabelResponse])
def list_labels(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    return db.query(Label).filter(Label.organization_id == org_id).all()

@router.patch("/{label_id}", response_model=LabelResponse)
def update_label(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    label_id: UUID,
    label_in: LabelUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    label = db.query(Label).filter(Label.id == label_id, Label.organization_id == org_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
        
    update_data = label_in.model_dump(exclude_unset=True)
    if 'name' in update_data and update_data['name'] != label.name:
        existing = db.query(Label).filter(Label.organization_id == org_id, Label.name == update_data['name']).first()
        if existing:
            raise HTTPException(status_code=400, detail="Label name already in use")
            
    for field, value in update_data.items():
        setattr(label, field, value)
    db.commit()
    db.refresh(label)
    return label

@router.delete("/{label_id}")
def delete_label(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    label_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    label = db.query(Label).filter(Label.id == label_id, Label.organization_id == org_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    db.delete(label)
    db.commit()
    return {"message": "Label deleted"}
