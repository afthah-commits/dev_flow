import os
import re

# Update analytics_service.py
file_path_as = "c:/personal_projects/devflow/backend/app/services/analytics_service.py"
with open(file_path_as, "r", encoding="utf-8") as f:
    as_content = f.read()

as_content = as_content.replace(
    "def get_dashboard_overview(db: Session, user_id: UUID) -> dict:",
    "def get_dashboard_overview(db: Session, org_id: UUID) -> dict:"
)
as_content = as_content.replace(
    "projects = db.query(Project).filter(Project.owner_id == user_id).all()",
    "projects = db.query(Project).filter(Project.organization_id == org_id).all()"
)
with open(file_path_as, "w", encoding="utf-8") as f:
    f.write(as_content)

# Update analytics.py
file_path_api = "c:/personal_projects/devflow/backend/app/api/v1/analytics.py"
with open(file_path_api, "r", encoding="utf-8") as f:
    api_content = f.read()

old_dash_def = """@router.get("/dashboard", response_model=DashboardOverview)
def get_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return get_dashboard_overview(db, current_user.id)"""

new_dash_def = """@router.get("/dashboard", response_model=DashboardOverview)
def get_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)
    return get_dashboard_overview(db, org_id)"""
    
api_content = api_content.replace(old_dash_def, new_dash_def)

# Update github analytics project auth check
# Let's replace get_project_auth with project organization membership
old_project_auth = """    get_project_auth(db, project_id, current_user.id)"""
new_project_auth = """    from app.models.project import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)"""

api_content = api_content.replace(old_project_auth, new_project_auth)

with open(file_path_api, "w", encoding="utf-8") as f:
    f.write(api_content)
    
print("analytics updated")
