import os

filepath = "c:/personal_projects/devflow/frontend/src/components/ProjectCard.tsx"
with open(filepath, "r") as f:
    content = f.read()

# Replace the generic task count mock with real stats
target = """      <div className="flex items-center justify-between mt-4">
        <span className="text-xs text-gray-500 font-medium">Updated {new Date(project.updated_at).toLocaleDateString()}</span>
      </div>"""

replacement = """      <div className="flex items-center justify-between mt-4">
        <span className="text-xs text-gray-500 font-medium">Updated {new Date(project.updated_at).toLocaleDateString()}</span>
        {project.task_stats && (
          <div className="flex gap-2 text-xs">
            <span className="text-gray-400" title="Total Tasks">{project.task_stats.total} tasks</span>
            {project.task_stats.in_progress > 0 && <span className="text-blue-400" title="In Progress">{project.task_stats.in_progress} active</span>}
            {project.task_stats.done > 0 && <span className="text-emerald-400" title="Done">{project.task_stats.done} done</span>}
          </div>
        )}
      </div>"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, "w") as f:
        f.write(content)
    print("ProjectCard.tsx updated")
else:
    print("Target string not found in ProjectCard.tsx")
