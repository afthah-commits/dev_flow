import os
import glob

# add getGlobalStats mock
test_files = [
    "c:/personal_projects/devflow/frontend/src/pages/Projects.test.tsx",
    "c:/personal_projects/devflow/frontend/src/App.test.tsx"
]

for p in test_files:
    if os.path.exists(p):
        with open(p, "r") as f:
            content = f.read()
            
        if "taskApi:" not in content:
            # We need to mock taskApi
            mock = """
vi.mock('../lib/taskApi', () => ({
  taskApi: { getGlobalStats: vi.fn().mockResolvedValue({ total: 0, done: 0, overdue: 0 }) }
}))
"""
            content = content.replace("describe(", mock + "\ndescribe(")
            
        with open(p, "w") as f:
            f.write(content)

print("Fixed mock")
