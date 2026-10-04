with open('backend/app/services/audit_service.py', 'r') as f:
    c = f.read()

c = c.replace('organization_id=uuid.UUID(str(organization_id))', 'organization_id=organization_id')

with open('backend/app/services/audit_service.py', 'w') as f:
    f.write(c)
