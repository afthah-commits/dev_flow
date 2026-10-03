with open('backend/app/main.py', 'r') as f:
    content = f.read()

if "from app.api.v1 import automations" not in content:
    content = content.replace(
        "from app.api.v1 import auth, users, projects, github, tasks, sprints, ai, analytics, audit, notifications, time, delivery, collaboration, search, ws",
        "from app.api.v1 import auth, users, projects, github, tasks, sprints, ai, analytics, audit, notifications, time, delivery, collaboration, search, ws, automations"
    )
    content = content.replace(
        "app.include_router(collaboration.router, prefix=\"/api/v1/collaboration\", tags=[\"collaboration\"])",
        "app.include_router(collaboration.router, prefix=\"/api/v1/collaboration\", tags=[\"collaboration\"])\napp.include_router(automations.router, prefix=\"/api/v1/automations\", tags=[\"automations\"])"
    )
    with open('backend/app/main.py', 'w') as f:
        f.write(content)
