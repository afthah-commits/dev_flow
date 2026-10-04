import re

with open(r"src/components/NotificationCenter.tsx", "r", encoding="utf-8") as f:
    content = f.read()

if "useRealtimeEvent" not in content:
    content = content.replace("import { Notification }", "import { useRealtimeEvent } from '../hooks/useRealtime';\nimport { Notification }")
    content = content.replace("const loadCount = async () => {", "useRealtimeEvent('notification.created', () => { loadCount(); if(open) loadNotifications(); });\n\n  const loadCount = async () => {")

with open(r"src/components/NotificationCenter.tsx", "w", encoding="utf-8") as f:
    f.write(content)
print("done")
