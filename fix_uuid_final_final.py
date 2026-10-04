import glob

files = glob.glob('backend/app/api/v1/*.py') + glob.glob('backend/app/services/*.py')
for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    modified = False
    
    if 'import uuid' not in content:
        content = 'import uuid\n' + content
        
    for k in ['APIKey(organization_id=organization_id', 'WebhookEndpoint(organization_id=organization_id', 'Integration(organization_id=organization_id', 'Automation(organization_id=organization_id']:
        if k in content:
            content = content.replace(k, k.replace('organization_id=organization_id', 'organization_id=uuid.UUID(str(organization_id))'))
            modified = True
            
    if 'AuditEvent(' in content:
        # replace any remaining organization_id=organization_id inside AuditEvent
        import re
        content = re.sub(r'AuditEvent\(\s*organization_id=organization_id', r'AuditEvent(organization_id=uuid.UUID(str(organization_id))', content)
        content = re.sub(r'AuditEvent\(\s*organization_id=org_id', r'AuditEvent(organization_id=uuid.UUID(str(org_id))', content)
        modified = True
        
    if modified:
        with open(f, 'w') as file:
            file.write(content)
