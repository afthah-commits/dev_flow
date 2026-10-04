with open('frontend/src/App.tsx', 'r') as f:
    c = f.read()

imports = '''import Security from './pages/settings/Security';
import Usage from './pages/settings/Usage';
import AdminSystem from './pages/AdminSystem';'''

c = c.replace("import ApiKeys from './pages/settings/ApiKeys';",
              "import ApiKeys from './pages/settings/ApiKeys';\n" + imports)

routes = '''              <Route path="/settings/security" element={<Security />} />
              <Route path="/settings/usage" element={<Usage />} />
              <Route path="/admin/system" element={<AdminSystem />} />'''

c = c.replace('<Route path="/settings/api-keys" element={<ApiKeys />} />',
              '<Route path="/settings/api-keys" element={<ApiKeys />} />\n' + routes)

with open('frontend/src/App.tsx', 'w') as f:
    f.write(c)
