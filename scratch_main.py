with open('backend/app/main.py', 'r') as f:
    content = f.read()
content = content.replace('from app.api.v1 import collaboration, search, ws, knowledge, clients, client_portal', 'from app.api.v1 import collaboration, search, ws, knowledge, clients, client_portal, workflows, custom_fields')
content = content.replace('app.include_router(client_portal.router, prefix=f"{settings.API_V1_STR}/client-portal", tags=["client-portal"])', 'app.include_router(client_portal.router, prefix=f"{settings.API_V1_STR}/client-portal", tags=["client-portal"])\napp.include_router(workflows.router, prefix=f"{settings.API_V1_STR}/workflows", tags=["workflows"])\napp.include_router(custom_fields.router, prefix=f"{settings.API_V1_STR}/custom-fields", tags=["custom-fields"])')
with open('backend/app/main.py', 'w') as f:
    f.write(content)
