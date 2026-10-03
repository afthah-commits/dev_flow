import sqlite3

conn = sqlite3.connect("c:/personal_projects/devflow/backend/devflow.db")
cursor = conn.cursor()

tables_to_drop = [
    "labels",
    "task_templates",
    "checklist_items",
    "task_dependencies",
    "task_labels",
    "task_watchers"
]

for table in tables_to_drop:
    try:
        cursor.execute(f"DROP TABLE {table}")
        print(f"Dropped {table}")
    except Exception as e:
        pass

for col in ["key", "task_seq_num"]:
    try:
        cursor.execute(f"ALTER TABLE projects DROP COLUMN {col}")
    except: pass

for col in ["task_key", "parent_id", "updated_by_id", "estimate_points", "estimate_hours", "actual_hours", "position", "is_blocked", "recurring_config"]:
    try:
        cursor.execute(f"ALTER TABLE tasks DROP COLUMN {col}")
    except: pass

conn.commit()
conn.close()
