for f in ['backend/app/api/v1/api_keys.py', 'backend/app/api/v1/webhooks.py', 'backend/app/api/v1/integrations.py', 'backend/app/services/automation_engine.py']:
    with open(f, 'r') as file:
        c = file.read()
    if 'organization_id=uuid.UUID(str(' not in c and 'organization_id=uuid.UUID(org_id)' not in c:
        print(f"Missing uuid coercion in {f}")
