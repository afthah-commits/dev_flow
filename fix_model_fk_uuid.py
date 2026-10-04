import glob

def fix(file):
    with open(file, 'r') as f:
        c = f.read()
    
    if 'from sqlalchemy import Column, String' in c and 'Uuid' not in c:
        c = c.replace('from sqlalchemy import Column, String', 'from sqlalchemy import Column, String, Uuid')
    elif 'from sqlalchemy import Column, String' in c:
        pass
        
    c = c.replace('organization_id = Column(String, ForeignKey("organizations.id")', 'organization_id = Column(Uuid, ForeignKey("organizations.id")')
    
    with open(file, 'w') as f:
        f.write(c)

for f in ['backend/app/models/api_key.py', 'backend/app/models/webhook.py', 'backend/app/models/integration.py']:
    fix(f)
