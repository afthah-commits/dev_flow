with open('backend/app/api/v1/delivery.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('deps.check_permission(db, current_user.id, org_id, "manage_releases")', 'deps.require_organization_member(db, current_user.id, org_id)')

with open('backend/app/api/v1/delivery.py', 'w', encoding='utf-8') as f:
    f.write(text)
