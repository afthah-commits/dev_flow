import os

file_path = "c:/personal_projects/devflow/backend/app/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

if "invitations" not in content:
    content = content.replace("import organizations, teams", "import organizations, teams, invitations")
    content = content.replace('tags=["teams"])\n', 'tags=["teams"])\napp.include_router(invitations.router, prefix=f"{settings.API_V1_STR}/invitations", tags=["invitations"])\n')
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
print("Added invitations router")
