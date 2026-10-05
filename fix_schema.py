import os

def fix_schema():
    path = "backend/app/schemas/daily_report.py"
    with open(path, "r") as f:
        content = f.read()

    # Import datetime as standard
    if "import datetime as pdt" not in content:
        content = "import datetime as pdt\n" + content
        
    content = content.replace("date: Optional[date] = None", "date: Optional[pdt.date] = None")
    content = content.replace("date: Optional['date'] = None", "date: Optional[pdt.date] = None")

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_schema()
