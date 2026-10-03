import os

file_path = "c:/personal_projects/devflow/frontend/src/App.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('import { AuthProvider } from "./hooks/useAuth";', 'import { AuthProvider } from "./hooks/useAuth";\nimport { OrganizationProvider } from "./contexts/OrganizationContext";')

content = content.replace('<AuthProvider>\n        <Routes>', '<AuthProvider>\n        <OrganizationProvider>\n          <Routes>')
content = content.replace('</Routes>\n      </AuthProvider>', '</Routes>\n        </OrganizationProvider>\n      </AuthProvider>')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("App.tsx updated")
