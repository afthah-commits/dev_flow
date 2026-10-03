import os

file_path = "c:/personal_projects/devflow/frontend/src/pages/ProjectDetails.tsx"
with open(file_path, "r") as f:
    content = f.read()

# 1. Add import
if "ProjectGitHub" not in content:
    content = content.replace("import { KanbanBoard } from '../components/KanbanBoard';", "import { KanbanBoard } from '../components/KanbanBoard';\nimport { ProjectGitHub } from '../components/ProjectGitHub';")

# 2. Add 'github' to view state
if "const [view, setView] = useState<'kanban' | 'list'>('kanban');" in content:
    content = content.replace("const [view, setView] = useState<'kanban' | 'list'>('kanban');", "const [view, setView] = useState<'kanban' | 'list' | 'github'>('kanban');")

# 3. Add GitHub button to header
btn_target = """          <button 
            onClick={() => setView('list')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              view === 'list' ? 'bg-blue-900/50 text-blue-400 border border-blue-800' : 'text-gray-400 hover:text-white'
            }`}
          >
            List View
          </button>"""
btn_replacement = btn_target + """
          <button 
            onClick={() => setView('github')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              view === 'github' ? 'bg-blue-900/50 text-blue-400 border border-blue-800' : 'text-gray-400 hover:text-white'
            }`}
          >
            GitHub
          </button>"""

if "GitHub" not in btn_target and btn_target in content:
    content = content.replace(btn_target, btn_replacement)

# 4. Render github view
view_target = """      {view === 'kanban' ? (
        <KanbanBoard tasks={tasks} onStatusChange={handleStatusChange} />
      ) : ("""

view_replacement = """      {view === 'github' ? (
        <ProjectGitHub project={project} />
      ) : view === 'kanban' ? (
        <KanbanBoard tasks={tasks} onStatusChange={handleStatusChange} />
      ) : ("""

if view_target in content:
    content = content.replace(view_target, view_replacement)
    
with open(file_path, "w") as f:
    f.write(content)

print("ProjectDetails.tsx updated")
