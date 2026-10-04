with open('backend/app/main.py', 'r') as f:
    content = f.read()

if "from app.api.v1 import integrations" not in content:
    content = content.replace(
        "from app.api.v1 import auth, users, projects, github, tasks, sprints, ai, analytics, audit, notifications, time, delivery, collaboration, search, ws, automations",
        "from app.api.v1 import auth, users, projects, github, tasks, sprints, ai, analytics, audit, notifications, time, delivery, collaboration, search, ws, automations, integrations, webhooks, api_keys\nfrom app.api.public_v1 import public"
    )
    content = content.replace(
        "app.include_router(automations.router, prefix=\"/api/v1/automations\", tags=[\"automations\"])",
        "app.include_router(automations.router, prefix=\"/api/v1/automations\", tags=[\"automations\"])\napp.include_router(integrations.router, prefix=\"/api/v1/integrations\", tags=[\"integrations\"])\napp.include_router(webhooks.router, prefix=\"/api/v1/webhooks\", tags=[\"webhooks\"])\napp.include_router(api_keys.router, prefix=\"/api/v1/api_keys\", tags=[\"api_keys\"])\napp.include_router(public.router, prefix=\"/api/public/v1\", tags=[\"public_api\"])"
    )
    with open('backend/app/main.py', 'w') as f:
        f.write(content)
