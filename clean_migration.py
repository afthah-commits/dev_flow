import re

with open('backend/alembic/versions/4ece17c722e2_phase_32_release_management_models.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace alter_column for UUID
pattern_num_to_uuid = r"\s*batch_op\.alter_column\('[^']+',\s*existing_type=sa\.NUMERIC\(\),\s*type_=sa\.UUID\(\)[^)]*\)"
pattern_uuid_to_num = r"\s*batch_op\.alter_column\('[^']+',\s*existing_type=sa\.UUID\(\),\s*type_=sa\.NUMERIC\(\)[^)]*\)"

text = re.sub(pattern_num_to_uuid, "", text)
text = re.sub(pattern_uuid_to_num, "", text)

# Remove empty blocks
lines = text.split('\n')
out_lines = []
skip = False
for i, line in enumerate(lines):
    if "with op.batch_alter_table" in line:
        # Check next lines to see if they only contain pass or nothing until next unindent
        j = i + 1
        empty = True
        while j < len(lines):
            if lines[j].strip() == "":
                pass
            elif lines[j].startswith("    with") or lines[j].startswith("    op.") or lines[j].startswith("def"):
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
        if line.startswith("    with") or line.startswith("    op.") or line.startswith("def"):
            skip = False
        else:
            continue
            
    out_lines.append(line)

with open('backend/alembic/versions/4ece17c722e2_phase_32_release_management_models.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))
