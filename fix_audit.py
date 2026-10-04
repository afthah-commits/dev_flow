with open('backend/app/api/v1/security.py', 'r') as f:
    c = f.read()

c = c.replace('from app.models.security import UserSession',
              'from app.models.security import UserSession\nfrom app.models.audit import AuditEvent')

c = c.replace('current_user.mfa_enabled = True',
              '''current_user.mfa_enabled = True
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="mfa.enabled"))''')

c = c.replace('current_user.mfa_enabled = False',
              '''current_user.mfa_enabled = False
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="mfa.disabled"))''')

c = c.replace('session.revoked_at = datetime.now()',
              '''session.revoked_at = datetime.now()
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="session.revoked"))''')

with open('backend/app/api/v1/security.py', 'w') as f:
    f.write(c)
