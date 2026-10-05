import os

def fix_schema():
    path = "backend/app/schemas/daily_report.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace("    date: date", "    date: pdt.date")

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_schema()
