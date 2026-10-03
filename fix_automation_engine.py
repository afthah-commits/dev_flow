with open('backend/app/services/automation_engine.py', 'r') as f:
    content = f.read()

content = content.replace("from app.models.project import Project, Task", "from app.models.project import Project\nfrom app.models.task import Task")

with open('backend/app/services/automation_engine.py', 'w') as f:
    f.write(content)
