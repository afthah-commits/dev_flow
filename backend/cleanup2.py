import sqlite3

conn = sqlite3.connect("c:/personal_projects/devflow/backend/devflow.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE projects DROP COLUMN key")
    print("Dropped projects.key")
except Exception as e:
    print(e)
    
try:
    cursor.execute("ALTER TABLE projects DROP COLUMN task_seq_num")
    print("Dropped projects.task_seq_num")
except Exception as e:
    print(e)

for col in ["task_key", "parent_id", "updated_by_id", "estimate_points", "estimate_hours", "actual_hours", "position", "is_blocked", "recurring_config"]:
    try:
        cursor.execute(f"ALTER TABLE tasks DROP COLUMN {col}")
        print(f"Dropped tasks.{col}")
    except Exception as e:
        print(e)

conn.commit()
conn.close()
