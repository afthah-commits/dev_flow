with open('backend/app/api/v1/organizations.py', 'r') as f:
    c = f.read()

c = c.replace('db: Session = Depends(get_db),', 'db: Session = Depends(deps.get_db),')
c = c.replace('current_user: User = Depends(get_current_user)', 'current_user: User = Depends(deps.get_current_user)')
c = c.replace('require_organization_member(db, current_user.id, organization_id)', 'deps.require_organization_member(db, current_user.id, organization_id)')

with open('backend/app/api/v1/organizations.py', 'w') as f:
    f.write(c)
