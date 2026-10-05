import os
import re

def fix_all():
    files = ["backend/app/services/analytics_service.py", "backend/app/api/v1/analytics.py"]
    for path in files:
        with open(path, "r") as f:
            content = f.read()
        
        # Replace str(var) with var for any variable ending with _id
        # Wait, using regex to catch == str(something_id)
        content = re.sub(r'==\s*str\(([a-zA-Z0-9_]+_id)\)', r'== \1', content)
        
        with open(path, "w") as f:
            f.write(content)

if __name__ == "__main__":
    fix_all()
