with open('frontend/src/components/layout/SettingsLayout.tsx', 'r') as f:
    c = f.read()

c = c.replace("{ id: 'organizations', label: 'Organizations', icon: Building2, path: '/settings/organizations' },",
              "{ id: 'organizations', label: 'Organizations', icon: Building2, path: '/settings/organizations' },\n  { id: 'security', label: 'Security Center', icon: Shield, path: '/settings/security' },\n  { id: 'usage', label: 'Organization Usage', icon: Activity, path: '/settings/usage' },")

c = c.replace("import { Settings, User, Building2, Key, Webhook, Link, Bell } from 'lucide-react';",
              "import { Settings, User, Building2, Key, Webhook, Link, Bell, Shield, Activity } from 'lucide-react';")

with open('frontend/src/components/layout/SettingsLayout.tsx', 'w') as f:
    f.write(c)
