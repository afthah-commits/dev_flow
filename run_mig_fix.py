import re
import glob

# Find latest migration
files = glob.glob('backend/alembic/versions/*_phase_32_release_models.py')
files.sort()
filename = files[-1]

with open(filename, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix foreign key constraint name
text = text.replace("batch_op.create_foreign_key(None, 'users', ['approved_by_id'], ['id']", "batch_op.create_foreign_key('fk_releases_approved_by_id', 'users', ['approved_by_id'], ['id']")
text = text.replace("batch_op.drop_constraint(None, type_='foreignkey')", "batch_op.drop_constraint('fk_releases_approved_by_id', type_='foreignkey')")

# Fix empty with blocks
def clean_empty_with_blocks(content):
    lines = content.split('\n')
    out_lines = []
    skip = False
    for i, line in enumerate(lines):
        if "with op.batch_alter_table" in line:
            j = i + 1
            empty = True
            while j < len(lines):
                if lines[j].strip() == "":
                    pass
                elif lines[j].startswith("    with") or lines[j].startswith("    op.") or lines[j].startswith("def") or lines[j].startswith("    # ### end"):
                    break
                else:
                    empty = False
                    break
                j += 1
            if empty:
                skip = True
                continue
        if skip:
            if line.strip() == "" or line.startswith("        #"):
                continue
            if line.startswith("    with") or line.startswith("    op.") or line.startswith("def") or line.startswith("    # ### end"):
                skip = False
            else:
                continue
                
        out_lines.append(line)
    return '\n'.join(out_lines)

# Remove UUID alter columns
pattern_num_to_uuid = r"\s*batch_op\.alter_column\('[^']+',\s*existing_type=sa\.NUMERIC\(\),\s*type_=sa\.UUID\(\)[^)]*\)"
pattern_uuid_to_num = r"\s*batch_op\.alter_column\('[^']+',\s*existing_type=sa\.UUID\(\),\s*type_=sa\.NUMERIC\(\)[^)]*\)"
text = re.sub(pattern_num_to_uuid, "", text)
text = re.sub(pattern_uuid_to_num, "", text)

text = clean_empty_with_blocks(text)

with open(filename, 'w', encoding='utf-8') as f:
    f.write(text)
