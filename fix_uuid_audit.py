import glob
import re

files = glob.glob('backend/app/api/v1/*.py') + glob.glob('backend/app/services/*.py')
for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    if 'AuditEvent(' in content and ('api_key' in f or 'integrations' in f or 'webhooks' in f or 'automation' in f):
        if 'import uuid' not in content:
            content = "import uuid\n" + content
        content = re.sub(r'organization_id=([a-zA-Z0-9_]+),', r'organization_id=uuid.UUID(str(\1)),', content)
        with open(f, 'w') as file:
            file.write(content)
