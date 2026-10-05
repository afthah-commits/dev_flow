import os

def fix_audit():
    path = "backend/app/api/v1/daily_reports.py"
    with open(path, "r") as f:
        content = f.read()

    # Replacements
    content = content.replace("actor_id=", "actor_user_id=")
    content = content.replace('action="', 'event_type="')
    content = content.replace("target_id=", "entity_id=")
    content = content.replace("target_type=", "entity_type=")
    content = content.replace("details=", "metadata_=")

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_audit()
