import re

with open('backend/app/api/v1/delivery.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace PLANNED with READY in plan
text = text.replace("ReleaseStatus.PLANNED", "ReleaseStatus.READY")
# Replace RELEASED with DEPLOYED
text = text.replace("ReleaseStatus.RELEASED", "ReleaseStatus.DEPLOYED")

with open('backend/app/api/v1/delivery.py', 'w', encoding='utf-8') as f:
    f.write(text)

# Also fix the test
with open('backend/tests/test_delivery.py', 'r', encoding='utf-8') as f:
    test_text = f.read()

test_text = test_text.replace('"status": "PLANNED"', '"status": "READY"')
test_text = test_text.replace('"status": "RELEASED"', '"status": "DEPLOYED"')
test_text = test_text.replace('assert r["status"] == "PLANNED"', 'assert r["status"] == "READY"')
test_text = test_text.replace('assert r["status"] == "RELEASED"', 'assert r["status"] == "DEPLOYED"')
test_text = test_text.replace('assert d["status"] == "SUCCESS"', 'assert d["status"] == "SUCCESS"')

with open('backend/tests/test_delivery.py', 'w', encoding='utf-8') as f:
    f.write(test_text)
