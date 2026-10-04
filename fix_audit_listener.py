import re

with open('backend/app/db/audit_listener.py', 'r') as f:
    c = f.read()

if 'import uuid' not in c:
    c = "import uuid\n" + c

# Replace e_org_id = getattr(obj, "organization_id", org_id)
# with a safe coercion function
c = c.replace('e_org_id = getattr(obj, "organization_id", org_id)', 'e_org_id = getattr(obj, "organization_id", org_id)\n            if isinstance(e_org_id, str): e_org_id = uuid.UUID(e_org_id)')

# Replace user_id which might also be a string?
# wait user_id is from session, usually Uuid or None. Let's make sure e_org_id is good.
# Also e_project_id, etc.
c = c.replace('e_project_id = getattr(obj, "project_id", project_id)', 'e_project_id = getattr(obj, "project_id", project_id)\n            if isinstance(e_project_id, str): e_project_id = uuid.UUID(e_project_id)')
c = c.replace('e_team_id = getattr(obj, "team_id", team_id)', 'e_team_id = getattr(obj, "team_id", team_id)\n            if isinstance(e_team_id, str): e_team_id = uuid.UUID(e_team_id)')


with open('backend/app/db/audit_listener.py', 'w') as f:
    f.write(c)
