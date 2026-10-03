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
        print(f"Error dropping {table}: {e}")

# Check if projects was altered
try:
    cursor.execute("ALTER TABLE projects DROP COLUMN task_seq_num")
    cursor.execute("ALTER TABLE projects DROP COLUMN key")
except:
    pass

try:
    cursor.execute("ALTER TABLE tasks DROP COLUMN task_key")
    cursor.execute("ALTER TABLE tasks DROP COLUMN parent_id")
    cursor.execute("ALTER TABLE tasks DROP COLUMN updated_by_id")
    cursor.execute("ALTER TABLE tasks DROP COLUMN estimate_points")
    cursor.execute("ALTER TABLE tasks DROP COLUMN estimate_hours")
    cursor.execute("ALTER TABLE tasks DROP COLUMN actual_hours")
    cursor.execute("ALTER TABLE tasks DROP COLUMN position")
    cursor.execute("ALTER TABLE tasks DROP COLUMN is_blocked")
    cursor.execute("ALTER TABLE tasks DROP COLUMN recurring_config")
except:
    pass

conn.commit()
conn.close()
