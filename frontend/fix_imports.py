import os

def replace_in_file(path, old, new):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

replace_in_file("c:/personal_projects/devflow/frontend/src/lib/organizationApi.ts", 
                "import api from './api';", 
                "import api from './axios';")

replace_in_file("c:/personal_projects/devflow/frontend/src/contexts/OrganizationContext.tsx", 
                "import api from '../lib/api';", 
                "import api from '../lib/axios';")

# fix 'o' implicitly has 'any' type
replace_in_file("c:/personal_projects/devflow/frontend/src/contexts/OrganizationContext.tsx", 
                "o => o.id", 
                "(o: Organization) => o.id")
                
# wait, there are two instances of o => o.id
replace_in_file("c:/personal_projects/devflow/frontend/src/contexts/OrganizationContext.tsx", 
                "o => o.id", 
                "(o: Organization) => o.id")

print("Fixed imports and types")
