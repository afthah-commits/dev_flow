import os

file_path = "c:/personal_projects/devflow/backend/app/api/v1/dashboard.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("from app.api import deps", "from app.api import deps\nfrom uuid import UUID\nfrom fastapi import HTTPException")

old_def = """def get_dashboard_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:"""

new_def = """def get_dashboard_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)"""

content = content.replace(old_def, new_def)
content = content.replace("Project.owner_id == current_user.id", "Project.organization_id == org_id")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("dashboard.py updated")
