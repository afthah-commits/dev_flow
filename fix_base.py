with open('backend/app/db/base.py', 'r') as f:
    content = f.read()

import_str = "from app.models.automation import Automation, AutomationExecution, AutomationActionExecution\n"
if import_str not in content:
    content += import_str
    with open('backend/app/db/base.py', 'w') as f:
        f.write(content)
