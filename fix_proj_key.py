with open('backend/tests/test_p16.py', 'r') as f:
    c = f.read()

c = c.replace('"description": ""', '"description": "", "key": "P16"')

with open('backend/tests/test_p16.py', 'w') as f:
    f.write(c)
