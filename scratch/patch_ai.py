import re

with open('backend/app/api/v1/ai.py', 'r') as f:
    content = f.read()

content = re.sub(
    r'record_event\(db,\s*org_id,\s*current_user\.id,\s*"([^"]+)",\s*(\{.*?\})\)',
    r'record_event(db=db, organization_id=org_id, actor_user_id=current_user.id, event_type="\1", entity_type="KNOWLEDGE", metadata=\2)',
    content
)

with open('backend/app/api/v1/ai.py', 'w') as f:
    f.write(content)
