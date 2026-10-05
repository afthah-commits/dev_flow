import os
import glob

for filepath in glob.glob("frontend/src/pages/analytics/*.tsx"):
    with open(filepath, 'r') as f:
        content = f.read()
    content = content.replace("import api from '../../lib/api';", "import { api } from '../../lib/axios';")
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Updated {filepath}")
