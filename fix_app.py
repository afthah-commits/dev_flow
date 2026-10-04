with open('frontend/src/App.tsx', 'r') as f:
    c = f.read()

imports = '''import Automations from './pages/Automations';
import AutomationDetails from './pages/AutomationDetails';
import Integrations from './pages/settings/Integrations';
import Webhooks from './pages/settings/Webhooks';
import ApiKeys from './pages/settings/ApiKeys';
'''

if 'import Automations from' not in c:
    c = c.replace('import Dashboard from', imports + 'import Dashboard from')
    with open('frontend/src/App.tsx', 'w') as f:
        f.write(c)
