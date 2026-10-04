import sys

file_path = 'frontend/src/pages/jobs/JobCenter.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("`http://localhost:8000/api/v1", "`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
