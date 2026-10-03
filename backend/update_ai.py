import os
import re

# Update ai.py
file_path_ai = "c:/personal_projects/devflow/backend/app/api/v1/ai.py"
with open(file_path_ai, "r", encoding="utf-8") as f:
    ai_content = f.read()

old_proj_check = """        proj = db.query(Project).filter(Project.id == request.project_id, Project.owner_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")"""

new_proj_check = """        proj = db.query(Project).filter(Project.id == request.project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        deps.require_organization_member(db, current_user.id, proj.organization_id)"""

ai_content = ai_content.replace(old_proj_check, new_proj_check)

with open(file_path_ai, "w", encoding="utf-8") as f:
    f.write(ai_content)

# Update context.py
file_path_ctx = "c:/personal_projects/devflow/backend/app/services/ai/context.py"
with open(file_path_ctx, "r", encoding="utf-8") as f:
    ctx_content = f.read()

ctx_content = ctx_content.replace(
    "project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user_id).first()",
    "project = db.query(Project).filter(Project.id == project_id).first()"
)
# No need to add deps.require_organization_member here as it's an internal service and API already verifies
# But wait, github context might need it. Let's make sure it doesn't fail.
with open(file_path_ctx, "w", encoding="utf-8") as f:
    f.write(ctx_content)

print("ai updated")
