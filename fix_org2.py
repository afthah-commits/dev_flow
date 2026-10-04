with open('backend/app/models/organization.py', 'r') as f:
    c = f.read()

c = c.replace('MEMBER = "MEMBER"', 'MEMBER = "MEMBER"\n    CUSTOM = "CUSTOM"')

with open('backend/app/models/organization.py', 'w') as f:
    f.write(c)
