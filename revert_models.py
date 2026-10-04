import glob
for f in ['backend/app/models/api_key.py', 'backend/app/models/webhook.py', 'backend/app/models/integration.py', 'backend/app/models/automation.py']:
    with open(f, 'r') as file:
        c = file.read()
    c = c.replace('organization_id = Column(Uuid, ForeignKey("organizations.id")', 'organization_id = Column(String, ForeignKey("organizations.id")')
    with open(f, 'w') as file:
        file.write(c)
