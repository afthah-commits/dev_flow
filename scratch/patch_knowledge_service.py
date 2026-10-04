import re

with open('backend/app/services/knowledge_service.py', 'r') as f:
    content = f.read()

content = re.sub(
    r'record_event\(db,\s*org_id,\s*user_id,\s*"([^"]+)",\s*(\{.*?\})\)',
    r'record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="\1", entity_type="KNOWLEDGE", metadata=\2)',
    content
)

with open('backend/app/services/knowledge_service.py', 'w') as f:
    f.write(content)
