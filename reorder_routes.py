import os

def reorder_routes():
    path = "backend/app/api/v1/daily_reports.py"
    with open(path, "r") as f:
        content = f.read()

    # Find where @router.get("/{report_id}" starts
    idx = content.find('@router.get("/{report_id}"')
    
    # We want to extract the new static routes we appended at the bottom
    # They start at "@router.get("/summary/range""
    # No wait, check_admin_or_owner is defined there too.
    idx_summary = content.find('def check_admin_or_owner')
    
    if idx != -1 and idx_summary != -1 and idx_summary > idx:
        part1 = content[:idx]
        dynamic_routes = content[idx:idx_summary]
        static_routes = content[idx_summary:]
        
        new_content = part1 + static_routes + "\n" + dynamic_routes
        with open(path, "w") as f:
            f.write(new_content)

if __name__ == "__main__":
    reorder_routes()
