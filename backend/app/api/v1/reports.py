from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.organization import OrganizationRole, OrganizationMember
from app.models.security import RolePermission, Role
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse, ReportFilter
from app.core import reports as report_service

router = APIRouter()

def check_permission(db: Session, member: OrganizationMember, required_permission: str):
    if member.role in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
        return True
    if member.custom_role_id:
        role = db.query(Role).filter(Role.id == member.custom_role_id).first()
        if role:
            perms = [rp.permission for rp in role.permissions]
            if required_permission in perms:
                return True
    raise HTTPException(status_code=403, detail="Not authorized")

@router.get("/", response_model=List[ReportResponse])
def get_reports(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "reports.view")
    reports = db.query(Report).filter(Report.organization_id == str(org_id)).all()
    return reports

@router.post("/", response_model=ReportResponse)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "reports.create")
    report = Report(
        **report_in.model_dump(),
        organization_id=str(org_id),
        created_by_id=str(current_user.id)
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "reports.view")
    report = db.query(Report).filter(Report.id == report_id, Report.organization_id == str(org_id)).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.patch("/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: str,
    report_in: ReportUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "reports.edit")
    report = db.query(Report).filter(Report.id == report_id, Report.organization_id == str(org_id)).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    update_data = report_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)
        
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "reports.delete")
    report = db.query(Report).filter(Report.id == report_id, Report.organization_id == str(org_id)).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    return {"success": True}

@router.post("/{report_id}/data")
def get_report_data(
    report_id: str,
    filters: ReportFilter,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "reports.view")
    report = db.query(Report).filter(Report.id == report_id, Report.organization_id == str(org_id)).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    data = report_service.generate_report_data(db, str(org_id), report, filters)
    return {"data": data}

@router.post("/{report_id}/export")
def export_report_data(
    report_id: str,
    filters: ReportFilter,
    format: str = Query("json"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "reports.export")
    report = db.query(Report).filter(Report.id == report_id, Report.organization_id == str(org_id)).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    data = report_service.generate_report_data(db, str(org_id), report, filters)
    return {"data": data, "format": format}

