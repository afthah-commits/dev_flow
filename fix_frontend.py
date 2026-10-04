with open('frontend/src/types/index.ts', 'r') as f:
    c = f.read()

c = c.replace('last_login_at?: string;', 'last_login_at?: string;\n  mfa_enabled?: boolean;')
with open('frontend/src/types/index.ts', 'w') as f:
    f.write(c)

with open('frontend/src/pages/settings/Usage.tsx', 'r') as f:
    c2 = f.read()
    
c2 = c2.replace('../../context/OrganizationContext', '../../contexts/OrganizationContext')
with open('frontend/src/pages/settings/Usage.tsx', 'w') as f:
    f.write(c2)
