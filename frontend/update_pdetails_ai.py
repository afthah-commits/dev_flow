import os

file_path = "c:/personal_projects/devflow/frontend/src/pages/ProjectDetails.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

if "import { ProjectAI }" not in content:
    content = content.replace("import { ProjectGitHub } from '../components/ProjectGitHub';", "import { ProjectGitHub } from '../components/ProjectGitHub';\nimport { ProjectAI } from '../components/ProjectAI';")

if "const [view, setView] = useState<'kanban' | 'list' | 'github'>('kanban');" in content:
    content = content.replace("const [view, setView] = useState<'kanban' | 'list' | 'github'>('kanban');", "const [view, setView] = useState<'kanban' | 'list' | 'github' | 'ai'>('kanban');")

btn_target = """          <button 
            onClick={() => setView('github')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              view === 'github' ? 'bg-blue-900/50 text-blue-400 border border-blue-800' : 'text-gray-400 hover:text-white'
            }`}
          >
            GitHub
          </button>"""
btn_replacement = btn_target + """
          <button 
            onClick={() => setView('ai')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              view === 'ai' ? 'bg-blue-900/50 text-blue-400 border border-blue-800' : 'text-gray-400 hover:text-white'
            }`}
          >
            AI Assistant
          </button>"""

if "AI Assistant" not in content and btn_target in content:
    content = content.replace(btn_target, btn_replacement)

view_target = """      {view === 'github' ? (
        <ProjectGitHub project={project} />
      ) : """

view_replacement = """      {view === 'ai' ? (
        <ProjectAI project={project} />
      ) : view === 'github' ? (
        <ProjectGitHub project={project} />
      ) : """

if view_target in content and "ProjectAI project={project}" not in content:
    content = content.replace(view_target, view_replacement)
    
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("ProjectDetails.tsx updated with AI")
