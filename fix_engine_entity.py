with open('backend/app/services/automation_engine.py', 'r') as f:
    c = f.read()

c = c.replace('entity_id=execution.automation_id,', 'entity_id=uuid.UUID(str(execution.automation_id)),')

with open('backend/app/services/automation_engine.py', 'w') as f:
    f.write(c)
