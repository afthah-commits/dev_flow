with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

import_str = "import CollaborationAnalytics from './pages/CollaborationAnalytics';\n"
content = import_str + content

content = content.replace(
    "<Route path=\"/analytics/delivery\" element={<DeliveryAnalytics />} />",
    "<Route path=\"/analytics/delivery\" element={<DeliveryAnalytics />} />\n            <Route path=\"/analytics/collaboration\" element={<CollaborationAnalytics />} />"
)

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
