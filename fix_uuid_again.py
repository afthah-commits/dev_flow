import glob
import re

files = glob.glob('backend/app/api/v1/*.py') + glob.glob('backend/app/services/*.py')
for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    if 'uuid.UUID(' in content and ('api_key' in f or 'integrations' in f or 'webhooks' in f or 'automation' in f):
        # Revert all
        content = content.replace("organization_id=uuid.UUID(str(organization_id)),", "organization_id=organization_id,")
        content = content.replace("organization_id=uuid.UUID(str(org_id)),", "organization_id=org_id,")
        
        # Add specifically for AuditEvent
        content = content.replace("AuditEvent(organization_id=organization_id,", "AuditEvent(organization_id=uuid.UUID(str(organization_id)),")
        content = content.replace("AuditEvent(\n                organization_id=org_id,", "AuditEvent(\n                organization_id=uuid.UUID(str(org_id)),")
        
        with open(f, 'w') as file:
            file.write(content)
