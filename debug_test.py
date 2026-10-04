with open('backend/tests/test_p16.py', 'r') as f:
    c = f.read()

c = c.replace('client.post(f"/api/v1/projects?organization_id={org_id}", json={"name": "Proj P16", "description": ""}, headers=headers)', 'res_proj = client.post(f"/api/v1/projects?organization_id={org_id}", json={"name": "Proj P16", "description": ""}, headers=headers)\n    print("PROJECT CREATE RESPONSE:", res_proj.status_code, res_proj.json())\n    assert res_proj.status_code == 200')

with open('backend/tests/test_p16.py', 'w') as f:
    f.write(c)
