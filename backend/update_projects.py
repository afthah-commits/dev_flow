import os

file_path = "c:/personal_projects/devflow/backend/app/api/v1/projects.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace imports
if "OrganizationMember" not in content:
    content = content.replace("from app.models.user import User", 
                              "from app.models.user import User\nfrom app.models.organization import OrganizationMember\nfrom uuid import UUID")

# Replace generate_slug to just ensure UUID is imported safely if needed

# Update create_project
old_create_def = """@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:"""

new_create_def = """@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)"""

content = content.replace(old_create_def, new_create_def)

# Update slug uniqueness check in create_project
content = content.replace("Project.owner_id == current_user.id, Project.slug == slug", "Project.organization_id == org_id, Project.slug == slug")

# Update project creation
content = content.replace("owner_id=current_user.id,\n        slug=slug", "owner_id=current_user.id,\n        organization_id=org_id,\n        slug=slug")

# Update list_projects
old_list_def = """@router.get("", response_model=PaginatedProjectResponse)
def list_projects(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
    priority: Optional[ProjectPriority] = None,
    sort_by: str = Query("updated_at", pattern="^(created_at|updated_at|name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$")
) -> Any:"""

new_list_def = """@router.get("", response_model=PaginatedProjectResponse)
def list_projects(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
    priority: Optional[ProjectPriority] = None,
    sort_by: str = Query("updated_at", pattern="^(created_at|updated_at|name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$")
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)"""

# In case regex was not yet updated to pattern
old_list_def_regex = old_list_def.replace('pattern=', 'regex=')
if old_list_def_regex in content:
    content = content.replace(old_list_def_regex, new_list_def)
elif old_list_def in content:
    content = content.replace(old_list_def, new_list_def)

content = content.replace("query = db.query(Project).filter(Project.owner_id == current_user.id)", "query = db.query(Project).filter(Project.organization_id == org_id)")

# Fix get/update/delete 
def replace_project_lookup(endpoint_name):
    global content
    target = f"project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()"
    replacement = f"""project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)"""
    content = content.replace(target, replacement)
    
    # We also need to remove the existing 'if not project:' since we included it above to check before org access
    # Let's do a smarter replace
    pass

import re
content = re.sub(
    r"project = db\.query\(Project\)\.filter\(Project\.id == project_id, Project\.owner_id == current_user\.id\)\.first\(\)\n\s*if not project:\n\s*raise HTTPException\(status_code=404, detail=\"Project not found\"\)",
    r"""project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)""",
    content
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("projects.py updated")
