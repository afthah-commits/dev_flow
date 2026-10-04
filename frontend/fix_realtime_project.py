import re

with open(r"src/pages/ProjectDetails.tsx", "r", encoding="utf-8") as f:
    content = f.read()

if "useRealtimeEvent" not in content:
    content = content.replace("import { TaskForm }", "import { useRealtimeEvent } from '../hooks/useRealtime';\nimport { TaskForm }")
    content = content.replace("const fetchTasks = async () => {", "useRealtimeEvent('task.updated', (payload) => {\n      fetchTasks();\n      fetchStats();\n  });\n  useRealtimeEvent('task.created', (payload) => {\n      fetchTasks();\n      fetchStats();\n  });\n\n  const fetchTasks = async () => {")

with open(r"src/pages/ProjectDetails.tsx", "w", encoding="utf-8") as f:
    f.write(content)
print("done")
