import React, { useState, useEffect } from "react";
import { sprintApi } from "../lib/sprintApi";
import { taskApi } from "../lib/taskApi";
import { Button } from "./ui/Button";
import { SprintForm } from "./SprintForm";
import { KanbanBoard } from "./KanbanBoard";
import { TaskDetailModal } from "./TaskDetailModal";
import { SprintPlanning } from "./SprintPlanning";
import { TaskStatus } from "../types/task";

export function SprintDetails({ projectId, sprintId, onBack }: { projectId: string, sprintId: string, onBack: () => void }) {
  const [sprint, setSprint] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [burndown, setBurndown] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"overview" | "board" | "planning">("overview");
  const [showEditForm, setShowEditForm] = useState(false);
  const [viewingTask, setViewingTask] = useState<any>(null);

  useEffect(() => {
    loadSprintData();
  }, [sprintId]);

  const loadSprintData = async () => {
    setLoading(true);
    try {
      const [sData, stData, bData, tData] = await Promise.all([
        sprintApi.get(projectId, sprintId),
        sprintApi.getStats(projectId, sprintId),
        sprintApi.getBurndown(projectId, sprintId),
        taskApi.list(projectId, { sprint_id: sprintId, page_size: 100 })
      ]);
      setSprint(sData);
      setStats(stData);
      setBurndown(bData);
      setTasks(tData.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    try {
      await sprintApi.start(projectId, sprintId);
      loadSprintData();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed to start sprint");
    }
  };

  const handleComplete = async () => {
    if (window.confirm("Complete this sprint?")) {
      const move = window.prompt("Move incomplete tasks to: (Type 'backlog' or a target sprint ID, or leave blank to keep them here)");
      try {
        await sprintApi.complete(projectId, sprintId, move || undefined);
        loadSprintData();
      } catch (e: any) {
        alert(e.response?.data?.detail || "Failed to complete sprint");
      }
    }
  };

  const handleTaskMove = async (taskId: string, newStatus: TaskStatus, newPosition: number) => {
    setTasks(prev => prev.map((t: any) => t.id === taskId ? { ...t, status: newStatus, position: newPosition } : t));
    try {
      await taskApi.updateStatus(projectId, taskId, newStatus, newPosition);
      const [stData, bData] = await Promise.all([
        sprintApi.getStats(projectId, sprintId),
        sprintApi.getBurndown(projectId, sprintId)
      ]);
      setStats(stData);
      setBurndown(bData);
    } catch (err) {
      alert("Failed to move task");
      loadSprintData();
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!sprint) return <div>Sprint not found</div>;

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex justify-between items-start shrink-0">
        <div>
          <button onClick={onBack} className="text-sm text-blue-500 hover:text-blue-400 mb-2 inline-block">&larr; Back to sprints</button>
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <span className="font-mono text-gray-500 text-lg">{sprint.key}</span> {sprint.name}
            <span className={`text-xs px-2 py-1 rounded-full border ${sprint.status === 'ACTIVE' ? 'bg-blue-900/50 text-blue-300 border-blue-800' : 'bg-gray-800 text-gray-300 border-gray-700 font-normal'}`}>
              {sprint.status}
            </span>
          </h2>
          {sprint.goal && <p className="text-gray-400 mt-2 max-w-2xl">{sprint.goal}</p>}
        </div>
        <div className="flex space-x-3">
          {sprint.status === 'PLANNED' && <Button onClick={handleStart} className="bg-emerald-600 hover:bg-emerald-700">Start Sprint</Button>}
          {sprint.status === 'ACTIVE' && <Button onClick={handleComplete} className="bg-emerald-600 hover:bg-emerald-700">Complete Sprint</Button>}
          <Button variant="outline" onClick={() => setShowEditForm(true)}>Edit</Button>
        </div>
      </div>

      <div className="flex gap-4 border-b border-gray-800 shrink-0">
        <button onClick={() => setView('overview')} className={`px-4 py-2 border-b-2 font-medium text-sm transition-colors ${view === 'overview' ? 'border-blue-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}>Overview</button>
        <button onClick={() => setView('board')} className={`px-4 py-2 border-b-2 font-medium text-sm transition-colors ${view === 'board' ? 'border-blue-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}>Sprint Board</button>
        {sprint.status !== 'COMPLETED' && sprint.status !== 'CANCELLED' && (
          <button onClick={() => setView('planning')} className={`px-4 py-2 border-b-2 font-medium text-sm transition-colors ${view === 'planning' ? 'border-blue-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}>Sprint Planning</button>
        )}
      </div>

      <div className="flex-1 min-h-0 relative">
        {view === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                <span className="text-xs text-gray-500 block mb-1">Total Points</span>
                <span className="text-xl font-bold text-white">{stats?.total_points || 0}</span>
                {sprint.capacity && <span className="text-xs text-gray-500 ml-2">/ {sprint.capacity} cap</span>}
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                <span className="text-xs text-gray-500 block mb-1">Completed Points</span>
                <span className="text-xl font-bold text-emerald-400">{stats?.completed_points || 0}</span>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                <span className="text-xs text-gray-500 block mb-1">Remaining Points</span>
                <span className="text-xl font-bold text-amber-400">{stats?.remaining_points || 0}</span>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                <span className="text-xs text-gray-500 block mb-1">Tasks</span>
                <span className="text-xl font-bold text-white">{stats?.completed_tasks || 0} / {stats?.total_tasks || 0}</span>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                <span className="text-xs text-gray-500 block mb-1">Progress</span>
                <span className="text-xl font-bold text-blue-400">
                  {stats?.total_points ? Math.round((stats.completed_points / stats.total_points) * 100) : 0}%
                </span>
              </div>
            </div>

            {sprint.capacity && stats?.total_points > sprint.capacity && (
              <div className="bg-red-900/20 border border-red-800/50 rounded-lg p-4 text-red-400 text-sm">
                Warning: Sprint is over capacity by {stats.total_points - sprint.capacity} points.
              </div>
            )}

            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4">Burndown Chart</h3>
              <div className="h-64 flex items-center justify-center text-gray-500 border border-dashed border-gray-700 rounded">
                [Burndown Chart Placeholder - Recharts would render here]
              </div>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4">Team Workload</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-gray-300">
                  <thead className="border-b border-gray-800">
                    <tr>
                      <th className="pb-3 font-medium">Assignee</th>
                      <th className="pb-3 font-medium">Assigned Tasks</th>
                      <th className="pb-3 font-medium">Completed Tasks</th>
                      <th className="pb-3 font-medium">Story Points</th>
                      <th className="pb-3 font-medium">Remaining Points</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.values(
                      tasks.reduce((acc, t) => {
                        const assignee = t.assignee ? t.assignee.full_name : 'Unassigned';
                        if (!acc[assignee]) {
                          acc[assignee] = { name: assignee, tasks: 0, completed: 0, pts: 0, rem_pts: 0 };
                        }
                        acc[assignee].tasks++;
                        const pts = t.estimate_points || 0;
                        acc[assignee].pts += pts;
                        if (t.status === 'DONE') {
                          acc[assignee].completed++;
                        } else {
                          acc[assignee].rem_pts += pts;
                        }
                        return acc;
                      }, {} as any)
                    ).map((u: any, i) => (
                      <tr key={i} className="border-b border-gray-800 last:border-0">
                        <td className="py-3">{u.name}</td>
                        <td className="py-3">{u.tasks}</td>
                        <td className="py-3">{u.completed}</td>
                        <td className="py-3">{u.pts}</td>
                        <td className="py-3">{u.rem_pts}</td>
                      </tr>
                    ))}
                    {tasks.length === 0 && <tr><td colSpan={5} className="py-4 text-center text-gray-500">No tasks in sprint</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {view === 'board' && (
          <KanbanBoard tasks={tasks} onTaskMove={handleTaskMove} onTaskClick={(t: any) => setViewingTask(t)} />
        )}

        {view === 'planning' && (
          <SprintPlanning projectId={projectId} sprint={sprint} onUpdate={loadSprintData} />
        )}
      </div>

      {showEditForm && (
        <SprintForm 
          projectId={projectId} 
          initialData={sprint} 
          onClose={() => setShowEditForm(false)} 
          onSuccess={() => { setShowEditForm(false); loadSprintData(); }} 
        />
      )}

      {viewingTask && (
        <TaskDetailModal 
          task={viewingTask} 
          projectId={projectId} 
          onClose={() => setViewingTask(null)} 
          onUpdated={loadSprintData} 
          onEdit={() => {}}
          onDelete={() => {}}
        />
      )}
    </div>
  );
}
