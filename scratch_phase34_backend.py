import os
import re

def update_analytics_service():
    path = "backend/app/services/analytics_service.py"
    with open(path, "r") as f:
        content = f.read()

    new_execute = """def execute_analytics_query(db: Session, org_id: UUID, request: AnalyticsQueryRequest) -> AnalyticsQueryResponse:
    query_data = []
    
    if request.metric == "tasks.completed":
        # Check if group by date
        if request.group_by == "date":
            # Just dummy aggregations for now using the requested time range
            now = datetime.now(timezone.utc)
            start = request.date_from or (now - timedelta(days=30))
            end = request.date_to or now
            
            # Since SQLite doesn't have easy date_trunc, we will just return mock trends if grouped by date
            # But the requirement says "Avoid loading complete tables... use count, sum, group_by"
            # Actually, using func.date(Task.updated_at) works in SQLite and Postgres
            
            from sqlalchemy import cast, Date
            stmt = db.query(
                cast(Task.updated_at, Date).label('date'),
                func.count(Task.id).label('value')
            ).filter(
                Task.organization_id == str(org_id),
                Task.status == TaskStatus.DONE,
                Task.updated_at >= start,
                Task.updated_at <= end
            ).group_by(cast(Task.updated_at, Date)).all()
            
            for row in stmt:
                query_data.append({"date": row.date.strftime("%Y-%m-%d") if row.date else None, "value": row.value})
                
        else:
            val = db.query(Task).filter(Task.organization_id == str(org_id), Task.status == TaskStatus.DONE).count()
            query_data.append({"value": val})
            
    elif request.metric == "sprint.velocity":
        if request.group_by == "date":
            from sqlalchemy import cast, Date
            now = datetime.now(timezone.utc)
            start = request.date_from or (now - timedelta(days=30))
            end = request.date_to or now
            
            stmt = db.query(
                cast(Sprint.end_date, Date).label('date'),
                func.sum(Sprint.completed_points).label('value')
            ).filter(
                Sprint.organization_id == str(org_id),
                Sprint.end_date >= start,
                Sprint.end_date <= end
            ).group_by(cast(Sprint.end_date, Date)).all()
            
            for row in stmt:
                query_data.append({"date": row.date.strftime("%Y-%m-%d") if row.date else None, "value": row.value})
        else:
            val = db.query(func.sum(Sprint.completed_points)).filter(Sprint.organization_id == str(org_id)).scalar() or 0
            query_data.append({"value": val})

    elif request.metric == "deployments.success_rate":
        if request.group_by == "date":
            from sqlalchemy import cast, Date
            now = datetime.now(timezone.utc)
            start = request.date_from or (now - timedelta(days=30))
            end = request.date_to or now
            
            stmt_success = db.query(
                cast(Deployment.created_at, Date).label('date'),
                func.count(Deployment.id).label('value')
            ).filter(
                Deployment.organization_id == str(org_id),
                Deployment.status == "SUCCESS",
                Deployment.created_at >= start,
                Deployment.created_at <= end
            ).group_by(cast(Deployment.created_at, Date)).all()
            
            for row in stmt_success:
                query_data.append({"date": row.date.strftime("%Y-%m-%d") if row.date else None, "value": row.value})
        else:
            val = db.query(Deployment).filter(Deployment.organization_id == str(org_id), Deployment.status == "SUCCESS").count()
            query_data.append({"value": val})

    else:
        # Generic fallback
        query_data.append({"value": 0})

    return AnalyticsQueryResponse(metric=request.metric, data=query_data)
"""
    
    content = re.sub(
        r'def execute_analytics_query.*?return AnalyticsQueryResponse\(metric=request\.metric, data=\[\]\)',
        new_execute,
        content,
        flags=re.DOTALL
    )
    
    with open(path, "w") as f:
        f.write(content)

def update_analytics_api():
    path = "backend/app/api/v1/analytics.py"
    with open(path, "r") as f:
        content = f.read()

    new_export = """
@router.post("/export")
def export_analytics_data(
    *,
    request: AnalyticsQueryRequest,
    format: str = Query("csv"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.export")
    
    # Reuse query executor
    result = execute_analytics_query(db, org_id, request)
    
    # Note: the real DevFlow export engine uses StreamingResponse, 
    # but here we follow Phase 18 Report export which returns JSON payload with format
    return {"data": result.data, "format": format}
"""
    
    if "@router.post(\"/export\")" not in content:
        content += new_export
        
    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    update_analytics_service()
    update_analytics_api()
