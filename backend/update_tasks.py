import os
import re

file_path = "c:/personal_projects/devflow/backend/app/api/v1/tasks.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_func = """def get_project_or_404(db: Session, project_id: UUID, current_user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project"""

new_func = """def get_project_or_404(db: Session, project_id: UUID, current_user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)
    return project"""

content = content.replace(old_func, new_func)

# Also remove the check that only allows current_user to be assigned tasks (multi-tenant allows any org member)
# we can just allow assigning to anyone in the org
assignee_check_old = """    if task_in.assignee_id and task_in.assignee_id != current_user.id:
        raise HTTPException(status_code=400, detail="Cannot assign task to unauthorized user")"""
        
assignee_check_new = """    if task_in.assignee_id:
        deps.require_organization_member(db, task_in.assignee_id, project.organization_id)"""

content = content.replace(assignee_check_old, assignee_check_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("tasks.py updated")
