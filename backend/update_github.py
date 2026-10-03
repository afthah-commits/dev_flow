import os

file_path = "c:/personal_projects/devflow/backend/app/api/v1/github.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_auth = """def get_project_auth(db: Session, project_id: UUID, user_id: UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project"""

new_auth = """def get_project_auth(db: Session, project_id: UUID, user_id: UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, user_id, project.organization_id)
    return project"""

content = content.replace(old_auth, new_auth)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("github updated")
