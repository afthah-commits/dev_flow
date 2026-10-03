import os
import glob

test_files = glob.glob("c:/personal_projects/devflow/backend/tests/test_*.py")

for file_path in test_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1: intercept header creation and insert organization creation
    # Find `headers = {"Authorization": f"Bearer {token}"}`
    # Replace with:
    # headers = {"Authorization": f"Bearer {token}"}
    # org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers)
    # if org_res.status_code == 201:
    #     org_id = org_res.json()["id"]
    #     headers["X-Organization-Id"] = org_id

    # Wait, some tests use `headersA`, `headersB`
    import re
    # Match `headers[A-Z0-9]* = {"Authorization": f"Bearer {token[A-Z0-9]*}"}`
    def repl(m):
        var_name = m.group(1)
        token_var = m.group(2)
        return f"""{var_name} = {{"Authorization": f"Bearer {{{token_var}}}"}}
    org_res = client.post("/api/v1/organizations", json={{"name": "Test Org"}}, headers={var_name})
    if org_res.status_code == 201:
        {var_name}["X-Organization-Id"] = org_res.json()["id"]"""
        
    content = re.sub(r'(headers\w*) = \{"Authorization": f"Bearer \{([^}]+)\}"\}', repl, content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Tests updated with org creation")
