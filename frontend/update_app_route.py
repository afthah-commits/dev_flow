import os
import re

file_path = "c:/personal_projects/devflow/frontend/src/App.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('import { NotificationPreferences } from "./pages/NotificationPreferences";',
                          'import { NotificationPreferences } from "./pages/NotificationPreferences";\nimport OrganizationLayout from "./pages/OrganizationLayout";')

content = content.replace('<Route path="/settings/notifications" element={<NotificationPreferences />} />',
                          '<Route path="/settings/notifications" element={<NotificationPreferences />} />\n            <Route path="/organization" element={<OrganizationLayout />} />')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("App.tsx updated for Org Layout")
