with open('backend/app/api/v1/automations.py', 'r') as f:
    c = f.read()

c = c.replace('created_by=current_user.id,', 'created_by=str(current_user.id),')

with open('backend/app/api/v1/automations.py', 'w') as f:
    f.write(c)


with open('backend/app/api/public_v1/public.py', 'r') as f:
    c = f.read()

import re
c = c.replace('Project.organization_id == api_key.organization_id', 'Project.organization_id == uuid.UUID(str(api_key.organization_id))')

with open('backend/app/api/public_v1/public.py', 'w') as f:
    f.write(c)
