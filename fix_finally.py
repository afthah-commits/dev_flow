import glob

def fix(file):
    with open(file, 'r') as f:
        c = f.read()
    
    # We want APIKey, WebhookEndpoint, Integration to just take string organization_id
    c = c.replace('organization_id=uuid.UUID(str(organization_id))', 'organization_id=organization_id')
    c = c.replace('organization_id=uuid.UUID(str(org_id))', 'organization_id=org_id')
    
    # For AuditEvent, we need it to be UUID object.
    c = c.replace('AuditEvent(organization_id=organization_id', 'AuditEvent(organization_id=uuid.UUID(str(organization_id))')
    c = c.replace('AuditEvent(\n        organization_id=org_id', 'AuditEvent(\n        organization_id=uuid.UUID(str(org_id))')
    
    with open(file, 'w') as f:
        f.write(c)

for f in ['backend/app/api/v1/api_keys.py', 'backend/app/api/v1/webhooks.py', 'backend/app/api/v1/integrations.py']:
    fix(f)
