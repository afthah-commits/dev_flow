with open('backend/alembic/versions/4ece17c722e2_phase_32_release_management_models.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("    with op.batch_alter_table('workflows', schema=None) as batch_op:\n\n    # ### end Alembic commands ###", "    pass\n    # ### end Alembic commands ###")
text = text.replace("batch_op.create_foreign_key(None, 'users'", "batch_op.create_foreign_key('fk_releases_approved_by_id', 'users'")
text = text.replace("batch_op.drop_constraint(None, type_='foreignkey')", "batch_op.drop_constraint('fk_releases_approved_by_id', type_='foreignkey')")

with open('backend/alembic/versions/4ece17c722e2_phase_32_release_management_models.py', 'w', encoding='utf-8') as f:
    f.write(text)
