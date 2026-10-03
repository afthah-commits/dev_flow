import os

file_path = "c:/personal_projects/devflow/frontend/src/pages/ProjectDetails.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

if "import { ProjectAnalytics }" not in content:
    content = content.replace("import { ProjectAI } from '../components/ProjectAI';", "import { ProjectAI } from '../components/ProjectAI';\nimport { ProjectAnalytics } from '../components/ProjectAnalytics';")

if "const [view, setView] = useState<'kanban' | 'list' | 'github' | 'ai'>('kanban');" in content:
    content = content.replace("const [view, setView] = useState<'kanban' | 'list' | 'github' | 'ai'>('kanban');", "const [view, setView] = useState<'kanban' | 'list' | 'github' | 'ai' | 'analytics'>('kanban');")

btn_target = """          <button 
            onClick={() => setView('ai')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              view === 'ai' ? 'bg-blue-900/50 text-blue-400 border border-blue-800' : 'text-gray-400 hover:text-white'
            }`}
          >
            AI Assistant
          </button>"""
btn_replacement = btn_target + """
          <button 
            onClick={() => setView('analytics')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              view === 'analytics' ? 'bg-blue-900/50 text-blue-400 border border-blue-800' : 'text-gray-400 hover:text-white'
            }`}
          >
            Analytics
          </button>"""

if "Analytics" not in content and btn_target in content:
    content = content.replace(btn_target, btn_replacement)

view_target = """      {view === 'ai' ? (
        <ProjectAI project={project} />
      ) : """

view_replacement = """      {view === 'analytics' ? (
        <ProjectAnalytics project={project} />
      ) : view === 'ai' ? (
        <ProjectAI project={project} />
      ) : """

if view_target in content and "ProjectAnalytics project={project}" not in content:
    content = content.replace(view_target, view_replacement)
    
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("ProjectDetails.tsx updated with Analytics")
