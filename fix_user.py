import os

def fix_user_name():
    path = "backend/app/api/v1/daily_reports.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace("user.full_name", "user.name")

    with open(path, "w") as f:
        f.write(content)
        
    path2 = "backend/tests/api/v1/test_daily_report_intelligence.py"
    with open(path2, "r") as f:
        content2 = f.read()
    
    content2 = content2.replace("full_name = ", "name = ")
    
    with open(path2, "w") as f:
        f.write(content2)

if __name__ == "__main__":
    fix_user_name()
