with open('backend/alembic/versions/f24f953c5076_phase_17_custom_roles.py', 'r') as f:
    c = f.read()

c = c.replace("batch_op.create_foreign_key(None, 'roles', ['custom_role_id'], ['id'], ondelete='SET NULL')",
              "batch_op.create_foreign_key('fk_org_inv_custom_role_roles_id', 'roles', ['custom_role_id'], ['id'], ondelete='SET NULL')", 1)

c = c.replace("batch_op.create_foreign_key(None, 'roles', ['custom_role_id'], ['id'], ondelete='SET NULL')",
              "batch_op.create_foreign_key('fk_org_mem_custom_role_roles_id', 'roles', ['custom_role_id'], ['id'], ondelete='SET NULL')", 1)

with open('backend/alembic/versions/f24f953c5076_phase_17_custom_roles.py', 'w') as f:
    f.write(c)
