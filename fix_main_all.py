with open('backend/app/main.py', 'r') as f:
    content = f.read()

import_lines = '''
from app.api.v1 import automations, integrations, webhooks, api_keys
from app.api.public_v1 import public
'''
if "import automations" not in content:
    content = content.replace(
        "from app.api.v1 import collaboration, search, ws",
        "from app.api.v1 import collaboration, search, ws" + import_lines
    )

route_lines = '''
app.include_router(automations.router, prefix=f"{settings.API_V1_STR}/automations", tags=["automations"])
app.include_router(integrations.router, prefix=f"{settings.API_V1_STR}/integrations", tags=["integrations"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["webhooks"])
app.include_router(api_keys.router, prefix=f"{settings.API_V1_STR}/api_keys", tags=["api_keys"])
app.include_router(public.router, prefix=f"/api/public/v1", tags=["public"])
'''
if "include_router(automations.router" not in content:
    content = content.replace(
        "app.include_router(ws.router, prefix=f\"{settings.API_V1_STR}/ws\", tags=[\"websocket\"])",
        "app.include_router(ws.router, prefix=f\"{settings.API_V1_STR}/ws\", tags=[\"websocket\"])\n" + route_lines
    )

with open('backend/app/main.py', 'w') as f:
    f.write(content)
