import re
import glob

# Find latest migration
files = glob.glob('backend/alembic/versions/*_phase_32_release_management_models.py')
files.sort()
filename = files[-1]

with open(filename, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix foreign key constraint name
text = text.replace("batch_op.create_foreign_key(None, 'users', ['approved_by_id'], ['id']", "batch_op.create_foreign_key('fk_releases_approved_by_id', 'users', ['approved_by_id'], ['id']")
text = text.replace("batch_op.drop_constraint(None, type_='foreignkey')", "batch_op.drop_constraint('fk_releases_approved_by_id', type_='foreignkey')")

# Remove saved_searches logic
# Since it's multiline and regex might be tricky, I will just remove it using string replacement for the exact blocks or regex with re.DOTALL

# In upgrade():
pattern1 = r"    with op\.batch_alter_table\('saved_searches', schema=None\) as batch_op:.*?op\.drop_table\('saved_searches'\)"
text = re.sub(pattern1, "", text, flags=re.DOTALL)

# In downgrade():
pattern2 = r"    op\.create_table\('saved_searches',.*?with op\.batch_alter_table\('saved_searches', schema=None\) as batch_op:.*?(?=\s+with op\.batch_alter_table\('release_approvals')"
text = re.sub(pattern2, "", text, flags=re.DOTALL)

with open(filename, 'w', encoding='utf-8') as f:
    f.write(text)
