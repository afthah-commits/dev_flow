with open('frontend/src/App.tsx', 'r') as f:
    content = f.read()

imports = '''import Clients from './pages/Clients';
import ClientDashboard from './pages/ClientDashboard';
'''

content = content.replace('import KnowledgeBase from', imports + 'import KnowledgeBase from')

routes = '''
            <Route path="/settings/clients" element={<Clients />} />
            <Route path="/client" element={<ClientDashboard />} />
            <Route path="/client/knowledge" element={<ClientDashboard />} />
            <Route path="/analytics/clients" element={<Clients />} />
'''

content = content.replace('<Route path="/settings/integrations" element={<Integrations />} />', '<Route path="/settings/integrations" element={<Integrations />} />' + routes)

with open('frontend/src/App.tsx', 'w') as f:
    f.write(content)
