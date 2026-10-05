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
from app.schemas.daily_report import (
    DailyReportCreate, DailyReportUpdate, DailyReportResponse,
    DailyReportSummaryResponse, TeamDailyReportResponse,
    BlockerSummaryResponse, WeeklySummaryResponse, DailyTrendItem
)
from app.models.organization import OrganizationRole, OrganizationMember
from sqlalchemy import func
from datetime import timedelta

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

def check_admin_or_owner(db: Session, user_id: UUID, org_id: UUID):
    deps.require_organization_member(db, user_id, org_id, [OrganizationRole.ADMIN, OrganizationRole.OWNER])

@router.get("/summary/range", response_model=DailyReportSummaryResponse)
def get_daily_report_summary_range(
    date_from: date,
    date_to: date,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    check_admin_or_owner(db, current_user.id, organization_id)
    
    reports = db.query(DailyReport).filter(
        DailyReport.organization_id == organization_id,
        DailyReport.report_date >= date_from,
        DailyReport.report_date <= date_to
    ).all()
    
    completed = sum(len(r.completed_tasks) for r in reports)
    planned = sum(len(r.next_plan) for r in reports)
    blockers = sum(len(r.blockers) for r in reports if r.blockers != ['None'] and r.blockers != [])
    unique_users = len(set(r.author_user_id for r in reports))
    
    total_users = db.query(func.count(OrganizationMember.id)).filter(OrganizationMember.organization_id == organization_id).scalar() or 0
    days = (date_to - date_from).days + 1
    expected = total_users * days
    
    return DailyReportSummaryResponse(
        total_reports=len(reports),
        completed_task_count=completed,
        next_plan_count=planned,
        blocker_count=blockers,
        unique_contributors=unique_users,
        missing_reports=max(0, expected - len(reports))
    )

@router.get("/summary/daily", response_model=DailyReportSummaryResponse)
def get_daily_report_summary_daily(
    report_date: date,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    check_admin_or_owner(db, current_user.id, organization_id)
    
    reports = db.query(DailyReport).filter(
        DailyReport.organization_id == organization_id,
        DailyReport.report_date == report_date
    ).all()
    
    completed = sum(len(r.completed_tasks) for r in reports)
    planned = sum(len(r.next_plan) for r in reports)
    blockers = sum(len(r.blockers) for r in reports if r.blockers != ['None'] and r.blockers != [])
    unique_users = len(set(r.author_user_id for r in reports))
    
    total_users = db.query(func.count(OrganizationMember.id)).filter(OrganizationMember.organization_id == organization_id).scalar() or 0
    
    return DailyReportSummaryResponse(
        total_reports=len(reports),
        completed_task_count=completed,
        next_plan_count=planned,
        blocker_count=blockers,
        unique_contributors=unique_users,
        missing_reports=max(0, total_users - len(reports)),
        date=report_date
    )

@router.get("/summary/weekly", response_model=WeeklySummaryResponse)
def get_daily_report_summary_weekly(
    start_date: date,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    check_admin_or_owner(db, current_user.id, organization_id)
    end_date = start_date + timedelta(days=6)
    
    reports = db.query(DailyReport).filter(
        DailyReport.organization_id == organization_id,
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date
    ).all()
    
    completed = sum(len(r.completed_tasks) for r in reports)
    blockers = sum(len(r.blockers) for r in reports if r.blockers != ['None'] and r.blockers != [])
    
    trend_dict = {}
    for r in reports:
        dt = r.report_date
        if dt not in trend_dict:
            trend_dict[dt] = {"reports_submitted": 0, "completed_tasks": 0}
        trend_dict[dt]["reports_submitted"] += 1
        trend_dict[dt]["completed_tasks"] += len(r.completed_tasks)
        
    trend = [
        DailyTrendItem(date=dt, reports_submitted=v["reports_submitted"], completed_tasks=v["completed_tasks"])
        for dt, v in sorted(trend_dict.items())
    ]
    
    return WeeklySummaryResponse(
        start_date=start_date,
        end_date=end_date,
        total_reports=len(reports),
        completed_tasks=completed,
        blockers=blockers,
        trend=trend
    )

@router.get("/team", response_model=List[TeamDailyReportResponse])
def get_team_daily_reports(
    report_date: date,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    check_admin_or_owner(db, current_user.id, organization_id)
    
    reports = db.query(DailyReport, User).join(User, DailyReport.author_user_id == User.id).filter(
        DailyReport.organization_id == organization_id,
        DailyReport.report_date == report_date
    ).order_by(User.name).all()
    
    result = []
    for report, user in reports:
        report_dict = report.__dict__.copy()
        report_dict["author_name"] = user.name or user.email
        result.append(report_dict)
        
    return result

@router.get("/blockers", response_model=List[BlockerSummaryResponse])
def get_daily_reports_blockers(
    days: int = 7,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
):
    check_admin_or_owner(db, current_user.id, organization_id)
    
    import datetime
    start_date = datetime.date.today() - datetime.timedelta(days=days)
    
    reports = db.query(DailyReport, User).join(User, DailyReport.author_user_id == User.id).filter(
        DailyReport.organization_id == organization_id,
        DailyReport.report_date >= start_date
    ).all()
    
    blocker_map = {}
    for report, user in reports:
        for b in report.blockers:
            b_lower = b.strip().lower()
            if not b_lower or b_lower == "none":
                continue
            
            if b_lower not in blocker_map:
                blocker_map[b_lower] = {
                    "blocker": b.strip(),
                    "occurrences": 0,
                    "latest_report_date": report.report_date,
                    "reporters": set()
                }
                
            blocker_map[b_lower]["occurrences"] += 1
            if report.report_date > blocker_map[b_lower]["latest_report_date"]:
                blocker_map[b_lower]["latest_report_date"] = report.report_date
            blocker_map[b_lower]["reporters"].add(user.name or user.email)
            
    result = []
    for b in blocker_map.values():
        b["reporters"] = list(b["reporters"])
        result.append(b)
        
    return sorted(result, key=lambda x: x["occurrences"], reverse=True)

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



