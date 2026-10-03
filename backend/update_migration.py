import os
import re

file_path = "c:/personal_projects/devflow/backend/alembic/versions/73431a3a65f9_advanced_tasks.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We need to insert our data migration right before `with op.batch_alter_table('tasks', schema=None) as batch_op:` ends
# Wait, actually after `batch_op.add_column` calls, but before `create_index` or after the block. 
# A separate data migration block after `with op.batch_alter_table('tasks', ...):` is safer.

migration_logic = """
    # Data migration: Populate project.key and task.task_key
    connection = op.get_bind()
    
    # 1. Update Projects
    projects = connection.execute(sa.text("SELECT id, name FROM projects")).fetchall()
    for proj in projects:
        # Generate a key: e.g. "DevFlow" -> "DEV"
        name_parts = proj.name.upper().split()
        if len(name_parts) >= 2:
            key = name_parts[0][:1] + name_parts[1][:2]
        else:
            key = proj.name.upper()[:3]
        if not key.strip():
            key = "PROJ"
        # make it alphanumeric only
        key = ''.join(e for e in key if e.isalnum())
        
        # update project
        connection.execute(sa.text("UPDATE projects SET key = :key WHERE id = :id"), {"key": key, "id": proj.id})
        
        # 2. Update Tasks for this project
        tasks = connection.execute(sa.text("SELECT id FROM tasks WHERE project_id = :pid ORDER BY created_at ASC"), {"pid": proj.id}).fetchall()
        for idx, task in enumerate(tasks):
            seq = idx + 1
            task_key = f"{key}-{seq}"
            connection.execute(sa.text("UPDATE tasks SET task_key = :tkey, position = :pos WHERE id = :tid"), 
                               {"tkey": task_key, "pos": float(seq), "tid": task.id})
        
        # Update sequence
        connection.execute(sa.text("UPDATE projects SET task_seq_num = :seq WHERE id = :id"), {"seq": len(tasks), "id": proj.id})
        
"""

# inject right after the `with op.batch_alter_table('tasks', schema=None) as batch_op:` block ends
content = content.replace("    # ### end Alembic commands ###", migration_logic + "\n    # ### end Alembic commands ###")

# We also need to fix: batch_op.create_foreign_key(None, 'users', ['updated_by_id'], ['id'], ondelete='SET NULL')
# 'users' isn't right, the table is 'tasks', the referring table is 'users'. Wait.
# `create_foreign_key(constraint_name, referent_table, local_cols, remote_cols)`
# So: `batch_op.create_foreign_key('fk_tasks_updated_by_id_users', 'users', ['updated_by_id'], ['id'], ondelete='SET NULL')`
# And for parent_id: `batch_op.create_foreign_key('fk_tasks_parent_id_tasks', 'tasks', ['parent_id'], ['id'], ondelete='SET NULL')`
content = content.replace("batch_op.create_foreign_key(None, 'tasks', ['parent_id'], ['id'], ondelete='SET NULL')", 
                          "batch_op.create_foreign_key('fk_tasks_parent_id_tasks', 'tasks', ['parent_id'], ['id'], ondelete='SET NULL')")
content = content.replace("batch_op.create_foreign_key(None, 'users', ['updated_by_id'], ['id'], ondelete='SET NULL')",
                          "batch_op.create_foreign_key('fk_tasks_updated_by_id_users', 'users', ['updated_by_id'], ['id'], ondelete='SET NULL')")


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Migration script updated")
