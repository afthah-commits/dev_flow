with open('backend/app/db/audit_listener.py', 'r') as f:
    c = f.read()

c = c.replace('entity_id=info["entity_id"],', 'entity_id=uuid.UUID(str(info["entity_id"])) if isinstance(info["entity_id"], str) else info["entity_id"],')

with open('backend/app/db/audit_listener.py', 'w') as f:
    f.write(c)
