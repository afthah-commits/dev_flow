import os

file_path = "c:/personal_projects/devflow/frontend/src/pages/Projects.test.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("vi.mock('../lib/taskApi', () => ({\n  taskApi: { getGlobalStats: vi.fn().mockResolvedValue({ total: 0, done: 0, overdue: 0 }) }\n}))",
"""vi.mock('../lib/analyticsApi', () => ({
  analyticsApi: { getDashboard: vi.fn().mockResolvedValue({ 
    total_projects: 2, 
    active_projects: 1,
    completed_projects: 0,
    total_tasks: 0,
    completed_tasks: 0,
    in_progress_tasks: 0,
    overdue_tasks: 0
  }) }
}))""")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Projects.test.tsx updated")
