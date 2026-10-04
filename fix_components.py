import glob

files = glob.glob('frontend/src/pages/Automations.tsx') + glob.glob('frontend/src/pages/AutomationDetails.tsx') + glob.glob('frontend/src/pages/settings/*.tsx')

for file in files:
    with open(file, 'r') as f:
        c = f.read()
    
    # replace useAuth with useOrganization
    c = c.replace("import { useAuth } from '../hooks/useAuth';", "import { useOrganization } from '../contexts/OrganizationContext';")
    c = c.replace("import { useAuth } from '../../hooks/useAuth';", "import { useOrganization } from '../../contexts/OrganizationContext';")
    c = c.replace("const { currentOrganization } = useAuth();", "const { currentOrganization } = useOrganization();")
    
    with open(file, 'w') as f:
        f.write(c)

