with open('backend/tests/test_delivery.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('res.json()["status"] == "PLANNED"', 'res.json()["status"] == "READY"')
text = text.replace('res.json()["status"] == "RELEASED"', 'res.json()["status"] == "DEPLOYED"')
text = text.replace('== "PLANNED"', '== "READY"')
text = text.replace('== "RELEASED"', '== "DEPLOYED"')

with open('backend/tests/test_delivery.py', 'w', encoding='utf-8') as f:
    f.write(text)
