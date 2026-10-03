import os

filepath = "c:/personal_projects/devflow/backend/.env"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if "AI_PROVIDER" not in content:
    content += "\n# AI Configuration\n"
    content += "AI_PROVIDER=mock\n"
    content += "AI_API_KEY=\n"
    content += "AI_MODEL=\n"
    content += "AI_BASE_URL=\n"

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated .env")
