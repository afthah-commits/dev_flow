import os

def fix_user_name_orderby():
    path = "backend/app/api/v1/daily_reports.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace("User.full_name", "User.name")

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_user_name_orderby()
