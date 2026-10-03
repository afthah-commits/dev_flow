import os
import re

file_path = "c:/personal_projects/devflow/frontend/src/pages/ProjectDetails.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add import
if "TaskDetailModal" not in content:
    content = content.replace(
        'import { TaskForm } from "../components/TaskForm";',
        'import { TaskForm } from "../components/TaskForm";\nimport { TaskDetailModal } from "../components/TaskDetailModal";'
    )

# Add viewingTask state
if "viewingTask" not in content:
    content = content.replace(
        'const [editingTask, setEditingTask] = useState<Task | null>(null);',
        'const [editingTask, setEditingTask] = useState<Task | null>(null);\n  const [viewingTask, setViewingTask] = useState<Task | null>(null);'
    )

# Update onTaskClick in KanbanBoard
content = content.replace(
    'onTaskClick={(t: any) => { setEditingTask(t); setShowForm(true); }}',
    'onTaskClick={(t: any) => setViewingTask(t)}'
)

# Update Actions in Table
content = content.replace(
    '<button onClick={() => { setEditingTask(t); setShowForm(true); }} className="text-blue-400 hover:underline mr-3">Edit</button>',
    '<button onClick={() => setViewingTask(t)} className="text-blue-400 hover:underline mr-3">View</button>'
)

# Add TaskDetailModal rendering
modal_code = """
      {viewingTask && !showForm && (
        <TaskDetailModal 
          task={viewingTask} 
          projectId={project.id} 
          onClose={() => setViewingTask(null)} 
          onUpdated={() => {
             // reload task specifically or all data
             loadData();
             // update viewingTask state with new data if possible (simplified by just reloading list and finding it)
             taskApi.get(project.id, viewingTask.id).then(setViewingTask);
          }} 
          onEdit={() => { setShowForm(true); setEditingTask(viewingTask); }} 
          onDelete={() => handleDeleteTask(viewingTask.id)} 
        />
      )}
"""

if "TaskDetailModal task={viewingTask}" not in content:
    content = content.replace(
        '{showForm && (',
        modal_code + '\n      {showForm && ('
    )

# When deleting from form, it should also close viewingTask
content = content.replace(
    'setEditingTask(null);',
    'setEditingTask(null);\n      setViewingTask(null);'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated ProjectDetails.tsx")
