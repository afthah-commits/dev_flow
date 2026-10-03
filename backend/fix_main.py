import os

file_path = "c:/personal_projects/devflow/backend/app/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("import organizations, teams, invitations", "import organizations, teams\nfrom app.api.v1 import invitations")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed main.py imports")
