import os
import re

file_path = "c:/personal_projects/devflow/backend/alembic/versions/73431a3a65f9_advanced_tasks.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "sa.Column('task_seq_num', sa.Integer(), nullable=False)",
    "sa.Column('task_seq_num', sa.Integer(), server_default='0', nullable=False)"
)
content = content.replace(
    "sa.Column('position', sa.Float(), nullable=False)",
    "sa.Column('position', sa.Float(), server_default='0.0', nullable=False)"
)
content = content.replace(
    "sa.Column('is_blocked', sa.Boolean(), nullable=False)",
    "sa.Column('is_blocked', sa.Boolean(), server_default='0', nullable=False)"
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Added server_default to NOT NULL columns in migration.")
