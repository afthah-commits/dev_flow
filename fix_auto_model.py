with open('backend/app/models/automation.py', 'r') as f:
    c = f.read()

if 'from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON' in c:
    c = c.replace('from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON', 'from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Uuid')

c = c.replace('organization_id = Column(String, ForeignKey("organizations.id")', 'organization_id = Column(Uuid, ForeignKey("organizations.id")')

with open('backend/app/models/automation.py', 'w') as f:
    f.write(c)
