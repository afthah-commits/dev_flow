with open('backend/app/main.py', 'r') as f:
    c = f.read()

import re
if 'from app.api.v1 import roles, security, admin' not in c:
    c = c.replace('from app.api.v1 import automations, integrations, webhooks, api_keys', 'from app.api.v1 import automations, integrations, webhooks, api_keys, roles, security, admin')
    c = c.replace('app.include_router(public.router, prefix="/api/public/v1", tags=["public"])', 'app.include_router(public.router, prefix="/api/public/v1", tags=["public"])\napp.include_router(roles.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["roles"])\napp.include_router(security.router, prefix=f"{settings.API_V1_STR}/security", tags=["security"])\napp.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])')

with open('backend/app/main.py', 'w') as f:
    f.write(c)
