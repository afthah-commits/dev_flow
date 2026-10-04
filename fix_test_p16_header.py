with open('backend/tests/test_p16.py', 'r') as f:
    c = f.read()

c = c.replace(
    'client.post(f"/api/v1/projects?organization_id={org_id}", json={"name": "Proj P16", "description": ""}, headers=headers)',
    'headers_with_org = headers.copy()\n    headers_with_org["X-Organization-Id"] = org_id\n    res_proj = client.post("/api/v1/projects", json={"name": "Proj P16", "description": ""}, headers=headers_with_org)'
)

with open('backend/tests/test_p16.py', 'w') as f:
    f.write(c)
