with open('backend/app/api/v1/delivery.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("from app.models.audit import AuditEvent", "from app.services.audit_service import record_event")
text = text.replace('AuditEvent.log(db, org_id, current_user.id, "RELEASE_APPROVAL_REQUESTED", entity_id=release_id, entity_type="RELEASE")', 'record_event(db, org_id, "RELEASE_APPROVAL_REQUESTED", "RELEASE", actor_user_id=current_user.id, entity_id=release_id)')
text = text.replace('AuditEvent.log(db, org_id, current_user.id, "RELEASE_APPROVED", entity_id=approval.release_id, entity_type="RELEASE")', 'record_event(db, org_id, "RELEASE_APPROVED", "RELEASE", actor_user_id=current_user.id, entity_id=approval.release_id)')
text = text.replace('AuditEvent.log(db, org_id, current_user.id, "RELEASE_REJECTED", entity_id=approval.release_id, entity_type="RELEASE")', 'record_event(db, org_id, "RELEASE_REJECTED", "RELEASE", actor_user_id=current_user.id, entity_id=approval.release_id)')
text = text.replace('AuditEvent.log(db, org_id, current_user.id, "RELEASE_APPROVAL_REVOKED", entity_id=approval.release_id, entity_type="RELEASE")', 'record_event(db, org_id, "RELEASE_APPROVAL_REVOKED", "RELEASE", actor_user_id=current_user.id, entity_id=approval.release_id)')
text = text.replace('AuditEvent.log(db, org_id, current_user.id, "RELEASE_PROMOTED", entity_id=release.id, entity_type="RELEASE", details={"target_env": target_env})', 'record_event(db, org_id, "RELEASE_PROMOTED", "RELEASE", actor_user_id=current_user.id, entity_id=release.id, metadata={"target_env": target_env})')
text = text.replace('AuditEvent.log(db, org_id, current_user.id, "RELEASE_ROLLED_BACK", entity_id=release.id, entity_type="RELEASE")', 'record_event(db, org_id, "RELEASE_ROLLED_BACK", "RELEASE", actor_user_id=current_user.id, entity_id=release.id)')

with open('backend/app/api/v1/delivery.py', 'w', encoding='utf-8') as f:
    f.write(text)
