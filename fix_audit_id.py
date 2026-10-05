import os
import re

def fix_entity_id():
    path = "backend/app/api/v1/daily_reports.py"
    with open(path, "r") as f:
        content = f.read()

    # Replace entity_id=str(...) with entity_id=...
    content = re.sub(r'entity_id=str\((.*?)\)', r'entity_id=\1', content)

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_entity_id()
