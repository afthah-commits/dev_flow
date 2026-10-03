import os
import re

file_path = "c:/personal_projects/devflow/frontend/src/layouts/DashboardLayout.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('<Link to="/projects" className="hover:text-white transition-colors">Projects</Link>',
                          '<Link to="/projects" className="hover:text-white transition-colors">Projects</Link>\n          <Link to="/organization" className="hover:text-white transition-colors">Organization</Link>')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("DashboardLayout.tsx updated")
