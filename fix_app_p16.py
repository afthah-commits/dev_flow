with open('frontend/src/App.tsx', 'r') as f:
    content = f.read()

imports = '''import Integrations from './pages/settings/Integrations';
import Webhooks from './pages/settings/Webhooks';
import ApiKeys from './pages/settings/ApiKeys';
'''

routes = '''              <Route path="/settings/integrations" element={<Integrations />} />
              <Route path="/settings/webhooks" element={<Webhooks />} />
              <Route path="/settings/api-keys" element={<ApiKeys />} />
'''

if "import Integrations from" not in content:
    content = content.replace(
        "import AutomationDetails from './pages/AutomationDetails';",
        "import AutomationDetails from './pages/AutomationDetails';\n" + imports
    )
    content = content.replace(
        "<Route path=\"/automations/:id\" element={<AutomationDetails />} />",
        "<Route path=\"/automations/:id\" element={<AutomationDetails />} />\n" + routes
    )
    with open('frontend/src/App.tsx', 'w') as f:
        f.write(content)
