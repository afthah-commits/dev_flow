with open('backend/app/services/automation_engine.py', 'r') as f:
    content = f.read()

content = content.replace("from app.models.auth import User", "from app.models.user import User")

with open('backend/app/services/automation_engine.py', 'w') as f:
    f.write(content)
