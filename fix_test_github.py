with open('backend/tests/test_github.py', 'r') as f:
    content = f.read()

content = content.replace(
    'org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers2)',
    'org_res = client.post("/api/v1/organizations", json={"name": "Test Org 2", "slug": "test-org-2"}, headers=headers2)'
)

with open('backend/tests/test_github.py', 'w') as f:
    f.write(content)
