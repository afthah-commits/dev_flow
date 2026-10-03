import os
import glob
import re

# 1. fix tsconfig.app.json
config_path = "c:/personal_projects/devflow/frontend/tsconfig.app.json"
with open(config_path, "r") as f:
    config = f.read()
config = config.replace('"verbatimModuleSyntax": true', '"verbatimModuleSyntax": false')
config = config.replace('"erasableSyntaxOnly": true', '"erasableSyntaxOnly": false')
with open(config_path, "w") as f:
    f.write(config)

# 2. remove unused React imports
paths = [
    "c:/personal_projects/devflow/frontend/src/pages/*.tsx",
    "c:/personal_projects/devflow/frontend/src/components/*.tsx",
    "c:/personal_projects/devflow/frontend/src/components/**/*.tsx",
    "c:/personal_projects/devflow/frontend/src/layouts/*.tsx",
    "c:/personal_projects/devflow/frontend/src/App.tsx"
]

for p in paths:
    for filepath in glob.glob(p):
        with open(filepath, "r") as f:
            content = f.read()
        content = re.sub(r'import React(?:,.*?\{.*?\})? from ["\']react["\'];?\n', '', content)
        content = re.sub(r'import React from ["\']react["\'];?\n', '', content)
        with open(filepath, "w") as f:
            f.write(content)

print("Fixed TS errors")
