with open('frontend/src/types/api_key.ts', 'r') as f:
    c = f.read()

c = c.replace('organization_id: string;', 'organization_id: string;\n    name: string;')

with open('frontend/src/types/api_key.ts', 'w') as f:
    f.write(c)
