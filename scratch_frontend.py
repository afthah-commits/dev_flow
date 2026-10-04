def patch_app_tsx():
    with open('frontend/src/App.tsx', 'r') as f:
        content = f.read()

    # Add imports if not present
    imports = """import { Workflows } from './pages/Workflows';
import { WorkflowBuilder } from './pages/WorkflowBuilder';
import { WorkflowAnalytics } from './pages/WorkflowAnalytics';
"""
    if "import { Workflows }" not in content:
        content = content.replace("import { Clients } from './pages/Clients';", "import { Clients } from './pages/Clients';\n" + imports)

    # Add routes if not present
    routes = """
              <Route path="workflows" element={<Workflows />} />
              <Route path="workflows/:id" element={<WorkflowBuilder />} />
              <Route path="analytics/workflows" element={<WorkflowAnalytics />} />
"""
    if "path=\"workflows\"" not in content:
        content = content.replace("<Route path=\"clients\" element={<Clients />} />", "<Route path=\"clients\" element={<Clients />} />\n" + routes)

    with open('frontend/src/App.tsx', 'w') as f:
        f.write(content)

patch_app_tsx()
