from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.organization import OrganizationRole
from app.models.dashboard import Dashboard, DashboardWidget
from app.schemas.report import (
    DashboardCreate, DashboardUpdate, DashboardResponse,
    DashboardWidgetCreate, DashboardWidgetUpdate, DashboardWidgetResponse
)
from app.api.v1.reports import check_permission

router = APIRouter()

@router.get("/", response_model=List[DashboardResponse])
def get_dashboards(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "dashboards.view")
    dashboards = db.query(Dashboard).filter(Dashboard.organization_id == str(org_id)).all()
    return dashboards

@router.post("/", response_model=DashboardResponse)
def create_dashboard(
    dashboard_in: DashboardCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "dashboards.manage")
    dashboard = Dashboard(
        **dashboard_in.model_dump(),
        organization_id=str(org_id),
        created_by_id=str(current_user.id)
    )
    if dashboard.is_default:
        db.query(Dashboard).filter(Dashboard.organization_id == str(org_id)).update({"is_default": False})
    
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return dashboard

@router.patch("/{dashboard_id}", response_model=DashboardResponse)
def update_dashboard(
    dashboard_id: str,
    dashboard_in: DashboardUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "dashboards.manage")
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id, Dashboard.organization_id == str(org_id)).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    update_data = dashboard_in.model_dump(exclude_unset=True)
    if update_data.get("is_default"):
        db.query(Dashboard).filter(Dashboard.organization_id == str(org_id)).update({"is_default": False})
        
    for field, value in update_data.items():
        setattr(dashboard, field, value)
        
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return dashboard

@router.delete("/{dashboard_id}")
def delete_dashboard(
    dashboard_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "dashboards.manage")
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id, Dashboard.organization_id == str(org_id)).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    db.delete(dashboard)
    db.commit()
    return {"success": True}

@router.post("/{dashboard_id}/widgets", response_model=DashboardWidgetResponse)
def add_widget(
    dashboard_id: str,
    widget_in: DashboardWidgetCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "dashboards.manage")
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id, Dashboard.organization_id == str(org_id)).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
        
    widget = DashboardWidget(
        **widget_in.model_dump(),
        dashboard_id=dashboard.id
    )
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return widget

@router.patch("/{dashboard_id}/widgets/{widget_id}", response_model=DashboardWidgetResponse)
def update_widget(
    dashboard_id: str,
    widget_id: str,
    widget_in: DashboardWidgetUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "dashboards.manage")
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id, Dashboard.organization_id == str(org_id)).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
        
    widget = db.query(DashboardWidget).filter(DashboardWidget.id == widget_id, DashboardWidget.dashboard_id == dashboard.id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
        
    update_data = widget_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(widget, field, value)
        
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return widget

@router.delete("/{dashboard_id}/widgets/{widget_id}")
def delete_widget(
    dashboard_id: str,
    widget_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "dashboards.manage")
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id, Dashboard.organization_id == str(org_id)).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
        
    widget = db.query(DashboardWidget).filter(DashboardWidget.id == widget_id, DashboardWidget.dashboard_id == dashboard.id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
        
    db.delete(widget)
    db.commit()
    return {"success": True}

