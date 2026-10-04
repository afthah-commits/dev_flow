from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from typing import Dict, Any, List

from app.models.report import Report, ReportType
from app.models.project import Project
from app.models.task import Task
from app.models.sprint import Sprint
from app.models.time import TimeEntry
from app.models.delivery import Release
from app.schemas.report import ReportFilter

def apply_filters(query, model, filters: ReportFilter, organization_id: str):
    if hasattr(model, 'organization_id'):
        query = query.filter(model.organization_id == organization_id)
        
    if filters.date_from and hasattr(model, 'created_at'):
        query = query.filter(model.created_at >= filters.date_from)
    if filters.date_to and hasattr(model, 'created_at'):
        query = query.filter(model.created_at <= filters.date_to)
        
    if filters.project_id and hasattr(model, 'project_id'):
        query = query.filter(model.project_id == filters.project_id)
        
    if filters.assignee_id and hasattr(model, 'assignee_id'):
        query = query.filter(model.assignee_id == filters.assignee_id)
        
    if filters.status and hasattr(model, 'status'):
        query = query.filter(model.status == filters.status)
        
    return query

def generate_report_data(db: Session, organization_id: str, report: Report, filters: ReportFilter) -> Dict[str, Any]:
    if report.report_type == ReportType.PROJECT_OVERVIEW:
        query = db.query(
            Project.status, func.count(Project.id).label('count')
        )
        query = apply_filters(query, Project, filters, organization_id)
        results = query.group_by(Project.status).all()
        return {"project_status_distribution": [{"status": r.status, "count": r.count} for r in results]}
        
    elif report.report_type == ReportType.TASK_ANALYTICS:
        query = db.query(
            Task.status, func.count(Task.id).label('count')
        )
        query = apply_filters(query, Task, filters, organization_id)
        results = query.group_by(Task.status).all()
        return {"task_status_distribution": [{"status": r.status, "count": r.count} for r in results]}
        
    elif report.report_type == ReportType.TIME_TRACKING:
        query = db.query(
            TimeEntry.user_id, func.sum(TimeEntry.duration).label('total_seconds')
        )
        query = apply_filters(query, TimeEntry, filters, organization_id)
        results = query.group_by(TimeEntry.user_id).all()
        return {"time_tracked_by_user": [{"user_id": r.user_id, "hours": round(r.total_seconds / 3600, 2) if r.total_seconds else 0} for r in results]}
        
    # More report types can be implemented similarly
    return {"message": f"Data aggregation for {report.report_type.value} not fully implemented yet", "data": []}

