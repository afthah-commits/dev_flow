import os
import re

def update_api():
    path = "backend/app/api/v1/daily_reports.py"
    with open(path, "r") as f:
        content = f.read()

    new_imports = """
from app.schemas.daily_report import (
    DailyReportCreate, DailyReportUpdate, DailyReportResponse,
    DailyReportSummaryResponse, TeamDailyReportResponse,
    BlockerSummaryResponse, WeeklySummaryResponse, DailyTrendItem
)
from app.models.organization import OrganizationRole, OrganizationMember
from sqlalchemy import func
from datetime import timedelta
"""
    # Replace the existing from app.schemas.daily_report import ...
    content = re.sub(
        r"from app\.schemas\.daily_report import .*",
        new_imports.strip(),
        content
    )

    new_routes = """
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
    ).order_by(User.full_name).all()
    
    result = []
    for report, user in reports:
        report_dict = report.__dict__.copy()
        report_dict["author_name"] = user.full_name or user.email
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
            blocker_map[b_lower]["reporters"].add(user.full_name or user.email)
            
    result = []
    for b in blocker_map.values():
        b["reporters"] = list(b["reporters"])
        result.append(b)
        
    return sorted(result, key=lambda x: x["occurrences"], reverse=True)
"""

    if "@router.get(\"/summary/range\"" not in content:
        content = content + "\n" + new_routes
        with open(path, "w") as f:
            f.write(content)

if __name__ == "__main__":
    update_api()
