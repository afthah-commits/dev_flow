with open('frontend/src/App.tsx', 'r') as f:
    content = f.read()

if "import Automations" not in content:
    content = content.replace(
        "import ProjectDiscussions from './pages/ProjectDiscussions';",
        "import ProjectDiscussions from './pages/ProjectDiscussions';\nimport Automations from './pages/Automations';\nimport AutomationDetails from './pages/AutomationDetails';"
    )
    content = content.replace(
        "<Route path=\"/analytics/collaboration\" element={<CollaborationAnalytics />} />",
        "<Route path=\"/analytics/collaboration\" element={<CollaborationAnalytics />} />\n              <Route path=\"/automations\" element={<Automations />} />\n              <Route path=\"/automations/:id\" element={<AutomationDetails />} />"
    )
    with open('frontend/src/App.tsx', 'w') as f:
        f.write(content)
