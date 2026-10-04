import glob
files = glob.glob('backend/app/api/v1/*.py') + glob.glob('backend/app/services/*.py')
for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    if 'AuditEvent(' in content and ('api_key' in f or 'integrations' in f or 'webhooks' in f or 'automation_engine' in f):
        import re
        content = re.sub(r'action="([^"]+)"', r'event_type="\1"', content)
        content = re.sub(r'details=', r'metadata_=', content)
        content = re.sub(r'entity_id="new"', r'entity_id=None', content) # or skip entity_id string conversion
        
        with open(f, 'w') as file:
            file.write(content)
