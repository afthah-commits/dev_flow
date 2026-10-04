with open('backend/app/services/automation_engine.py', 'r') as f:
    content = f.read()

content = content.replace('action=action.get("audit_action", "AUTOMATION_CUSTOM_EVENT")', 'event_type=action.get("audit_action", "AUTOMATION_CUSTOM_EVENT")')
content = content.replace('details=action.get("details", {})', 'metadata_=action.get("details", {})')

with open('backend/app/services/automation_engine.py', 'w') as f:
    f.write(content)
