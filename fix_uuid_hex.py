import os

def patch_uuid_hex_bug():
    # 1. Patch analytics_service.py
    path1 = "backend/app/services/analytics_service.py"
    with open(path1, "r") as f:
        content = f.read()
    
    # Replace str(org_id) with org_id
    content = content.replace("== str(org_id)", "== org_id")
    content = content.replace("== str(project_id)", "== project_id")
    content = content.replace(".in_([str(p.id) for p in projects])", ".in_([p.id for p in projects])")
    content = content.replace(".in_(project_ids)", ".in_(project_ids)")
    
    with open(path1, "w") as f:
        f.write(content)

    # 2. Patch analytics.py
    path2 = "backend/app/api/v1/analytics.py"
    with open(path2, "r") as f:
        content = f.read()
        
    content = content.replace("== str(project_id)", "== project_id")
    
    with open(path2, "w") as f:
        f.write(content)

if __name__ == "__main__":
    patch_uuid_hex_bug()
