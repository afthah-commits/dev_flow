import sys
with open('app/main.py', 'r') as f:
    content = f.read()

content = content.replace('from app.api.v1 import automations', 'from app.api.v1 import reports, dashboards\nfrom app.api.v1 import automations')

if 'app.include_router(reports.router' not in content:
    content = content.replace('app.include_router(automations.router', 'app.include_router(reports.router, prefix=f\"{settings.API_V1_STR}/reports\", tags=[\"reports\"])\napp.include_router(dashboards.router, prefix=f\"{settings.API_V1_STR}/dashboards\", tags=[\"dashboards\"])\napp.include_router(automations.router')

with open('app/main.py', 'w') as f:
    f.write(content)
