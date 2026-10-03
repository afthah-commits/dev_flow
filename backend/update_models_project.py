import os
import re

file_path = "c:/personal_projects/devflow/backend/app/models/project.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add key and task_seq_num to Project
if "task_seq_num =" not in content:
    content = content.replace(
        'slug = Column(String, nullable=False, index=True)',
        'slug = Column(String, nullable=False, index=True)\n    key = Column(String, nullable=True, index=True)\n    task_seq_num = Column(Integer, default=0, nullable=False)'
    )
    content = "from sqlalchemy import Integer\n" + content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
print("Updated project.py")
