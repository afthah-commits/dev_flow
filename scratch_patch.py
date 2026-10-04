import re

# 1. Update Task
with open('backend/app/models/task.py', 'r') as f:
    task_content = f.read()
if "client_visible = Column" not in task_content:
    task_content = task_content.replace(
        'title = Column(String, nullable=False, index=True)',
        'client_visible = Column(Boolean, default=False, nullable=False, server_default="0")\n    title = Column(String, nullable=False, index=True)'
    )
    with open('backend/app/models/task.py', 'w') as f:
        f.write(task_content)

# 2. Update Comment
with open('backend/app/models/collaboration.py', 'r') as f:
    comment_content = f.read()
if "client_visible = Column" not in comment_content:
    comment_content = comment_content.replace(
        'is_pinned = Column(Boolean, default=False)',
        'is_pinned = Column(Boolean, default=False)\n    client_visible = Column(Boolean, default=False, nullable=False, server_default="0")'
    )
    with open('backend/app/models/collaboration.py', 'w') as f:
        f.write(comment_content)

# 3. Update AuditEvent
with open('backend/app/models/audit.py', 'r') as f:
    audit_content = f.read()
if "client_visible = Column" not in audit_content:
    audit_content = audit_content.replace(
        'user_agent = Column(String, nullable=True)',
        'user_agent = Column(String, nullable=True)\n    client_visible = Column(Boolean, default=False, nullable=False, server_default="0")'
    )
    with open('backend/app/models/audit.py', 'w') as f:
        f.write(audit_content)

# 4. Update SpaceVisibility
with open('backend/app/models/knowledge.py', 'r') as f:
    know_content = f.read()
if "CLIENTS =" not in know_content:
    know_content = know_content.replace(
        'ORGANIZATION = "ORGANIZATION"',
        'ORGANIZATION = "ORGANIZATION"\n    CLIENTS = "CLIENTS"\n    PUBLIC = "PUBLIC"'
    )
    with open('backend/app/models/knowledge.py', 'w') as f:
        f.write(know_content)

print('Models updated')
