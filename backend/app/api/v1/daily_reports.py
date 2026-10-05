import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.api import deps
from app.models.daily_report import DailyReport
from app.models.user import User
from app.models.audit import AuditEvent
from app.schemas.daily_report import DailyReportCreate, DailyReportUpdate, DailyReportResponse

router = APIRouter()

@router.get("/", response_model=List[DailyReportResponse])
def list_daily_reports(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    query = db.query(DailyReport).filter(DailyReport.organization_id == organization_id)
    if date_from:
        query = query.filter(DailyReport.report_date >= date_from)
    if date_to:
        query = query.filter(DailyReport.report_date <= date_to)
    
    reports = query.order_by(desc(DailyReport.report_date)).offset(skip).limit(limit).all()
    return reports

@router.post("/", response_model=DailyReportResponse)
def create_daily_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: DailyReportCreate,
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    # Check if duplicate
    existing = db.query(DailyReport).filter(
        DailyReport.organization_id == organization_id,
        DailyReport.author_user_id == current_user.id,
        DailyReport.report_date == report_in.report_date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="A report for this date already exists.")

    report = DailyReport(
        organization_id=organization_id,
        author_user_id=current_user.id,
        report_date=report_in.report_date,
        completed_tasks=report_in.completed_tasks,
        next_plan=report_in.next_plan,
        blockers=report_in.blockers
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Audit event
    audit_event = AuditEvent(
        organization_id=organization_id,
        actor_user_id=current_user.id,
        event_type="daily_report.created",
        entity_id=report.id,
        entity_type="daily_report",
        metadata_={"report_date": str(report.report_date)}
    )
    db.add(audit_event)
    db.commit()

    return report

@router.get("/{report_id}", response_model=DailyReportResponse)
def get_daily_report(
    report_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    report = db.query(DailyReport).filter(
        DailyReport.id == report_id,
        DailyReport.organization_id == organization_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Daily report not found")
    return report

@router.patch("/{report_id}", response_model=DailyReportResponse)
def update_daily_report(
    report_id: UUID,
    report_in: DailyReportUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    report = db.query(DailyReport).filter(
        DailyReport.id == report_id,
        DailyReport.organization_id == organization_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Daily report not found")
    
    # Enforce authorship or ownership (assuming simple authorship check for now)
    if report.author_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this report")

    update_data = report_in.model_dump(exclude_unset=True)
    
    if "report_date" in update_data and update_data["report_date"] != report.report_date:
        existing = db.query(DailyReport).filter(
            DailyReport.organization_id == organization_id,
            DailyReport.author_user_id == current_user.id,
            DailyReport.report_date == update_data["report_date"],
            DailyReport.id != report_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="A report for this date already exists.")
            
    for field, value in update_data.items():
        setattr(report, field, value)

    db.add(report)
    db.commit()
    db.refresh(report)

    audit_event = AuditEvent(
        organization_id=organization_id,
        actor_user_id=current_user.id,
        event_type="daily_report.updated",
        entity_id=report.id,
        entity_type="daily_report"
    )
    db.add(audit_event)
    db.commit()

    return report

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_daily_report(
    report_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    report = db.query(DailyReport).filter(
        DailyReport.id == report_id,
        DailyReport.organization_id == organization_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Daily report not found")
        
    if report.author_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this report")

    db.delete(report)
    
    audit_event = AuditEvent(
        organization_id=organization_id,
        actor_user_id=current_user.id,
        event_type="daily_report.deleted",
        entity_id=report_id,
        entity_type="daily_report"
    )
    db.add(audit_event)
    db.commit()

@router.post("/{report_id}/export")
def export_daily_report(
    report_id: UUID,
    format: str = "json",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    report = db.query(DailyReport).filter(
        DailyReport.id == report_id,
        DailyReport.organization_id == organization_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Daily report not found")

    audit_event = AuditEvent(
        organization_id=organization_id,
        actor_user_id=current_user.id,
        event_type="daily_report.exported",
        entity_id=report.id,
        entity_type="daily_report",
        metadata_={"format": format}
    )
    db.add(audit_event)
    db.commit()

    data = {
        "id": str(report.id),
        "date": str(report.report_date),
        "author": str(report.author_user_id),
        "completed_tasks": report.completed_tasks,
        "next_plan": report.next_plan,
        "blockers": report.blockers
    }
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Section", "Item"])
        for item in data["completed_tasks"]:
            writer.writerow(["Completed Task", item])
        for item in data["next_plan"]:
            writer.writerow(["Next Plan", item])
        for item in data["blockers"]:
            writer.writerow(["Blocker", item])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report_{report.report_date}.csv"}
        )
    else:
        return data

