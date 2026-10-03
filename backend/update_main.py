import os

file_path = "c:/personal_projects/devflow/backend/app/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("from app.api.v1 import auth, projects, tasks, dashboard, github, ai, analytics, notifications",
                          "from app.api.v1 import auth, projects, tasks, dashboard, github, ai, analytics, notifications, organizations, teams")

content = content.replace('app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])',
                          'app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])\napp.include_router(organizations.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["organizations"])\napp.include_router(teams.router, prefix=f"{settings.API_V1_STR}", tags=["teams"])')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("main.py updated")
