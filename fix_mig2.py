import re

with open('backend/alembic/versions/4ece17c722e2_phase_32_release_management_models.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the specific error
pattern = r"    with op\.batch_alter_table\('workflows', schema=None\) as batch_op:\s+# ### end Alembic commands ###"
text = re.sub(pattern, "    pass\n    # ### end Alembic commands ###", text)

with open('backend/alembic/versions/4ece17c722e2_phase_32_release_management_models.py', 'w', encoding='utf-8') as f:
    f.write(text)
