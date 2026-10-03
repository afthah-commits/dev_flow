import os

file_path = "c:/personal_projects/devflow/frontend/src/pages/Dashboard.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'import { taskApi } from "../lib/taskApi";\nimport { Project, ProjectStatus } from "../types/project";\nimport { TaskStats } from "../types/task";',
    'import { analyticsApi } from "../lib/analyticsApi";\nimport { Project } from "../types/project";\nimport { DashboardOverview } from "../types/analytics";'
)

content = content.replace(
    'const [taskStats, setTaskStats] = useState<TaskStats | null>(null);',
    'const [stats, setStats] = useState<DashboardOverview | null>(null);'
)

content = content.replace(
    'taskApi.getGlobalStats()',
    'analyticsApi.getDashboard()'
)

content = content.replace(
    'setTaskStats(stats);',
    'setStats(stats);'
)

content = content.replace(
    'const total = projects.length; // Approximate for recent\n  const active = projects.filter((p: any) => p.status === ProjectStatus.ACTIVE).length;\n  const completed = projects.filter((p: any) => p.status === ProjectStatus.COMPLETED).length;',
    ''
)

content = content.replace(
    '<span className="text-3xl font-bold mt-2 text-emerald-400">{active}</span>',
    '<span className="text-3xl font-bold mt-2 text-emerald-400">{stats?.active_projects || 0}</span>'
)
content = content.replace(
    '<span className="text-3xl font-bold mt-2 text-blue-400">{taskStats?.total || 0}</span>',
    '<span className="text-3xl font-bold mt-2 text-blue-400">{stats?.total_tasks || 0}</span>'
)
content = content.replace(
    '<span className="text-3xl font-bold mt-2 text-purple-400">{taskStats?.done || 0}</span>',
    '<span className="text-3xl font-bold mt-2 text-purple-400">{stats?.completed_tasks || 0}</span>'
)
content = content.replace(
    '<span className="text-3xl font-bold mt-2 text-red-400">{taskStats?.overdue || 0}</span>',
    '<span className="text-3xl font-bold mt-2 text-red-400">{stats?.overdue_tasks || 0}</span>'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Dashboard.tsx updated")
