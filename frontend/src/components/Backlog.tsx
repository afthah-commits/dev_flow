import React, { useState, useEffect } from "react";
import { backlogApi } from "../lib/backlogApi";
import { Project } from "../types/project";
import { TaskDetailModal } from "./TaskDetailModal";
import { TaskForm } from "./TaskForm";
import { taskApi } from "../lib/taskApi";

export function Backlog({ project }: { project: Project }) {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewingTask, setViewingTask] = useState<any>(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    loadBacklog();
  }, [project.id]);

  const loadBacklog = async () => {
    setLoading(true);
    try {
      const data = await backlogApi.get(project.id, { page_size: 100 });
      setTasks(data.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full space-y-4">
      <div className="flex justify-between items-center shrink-0">
        <h2 className="text-xl font-bold">Product Backlog</h2>
        <button onClick={() => setShowForm(true)} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium">Add Task</button>
      </div>

      <div className="flex-1 bg-gray-900 rounded-lg border border-gray-800 overflow-hidden flex flex-col min-h-0">
        {loading ? (
          <div className="p-4 text-gray-500">Loading backlog...</div>
        ) : (
          <div className="overflow-auto flex-1 p-4 space-y-2">
            {tasks.map(t => (
              <div key={t.id} onClick={() => setViewingTask(t)} className="bg-gray-800 border border-gray-700 rounded p-3 flex justify-between items-center cursor-pointer hover:border-gray-600">
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-white flex items-center gap-2">
                    <span className="text-xs text-gray-500 font-mono">{t.task_key}</span>
                    {t.title}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-400">
                  <span>{t.priority}</span>
                  <span className="px-2 py-1 bg-gray-900 rounded">{t.status.replace('_', ' ')}</span>
                  {t.estimate_points && <span>{t.estimate_points} pts</span>}
                </div>
              </div>
            ))}
            {tasks.length === 0 && <div className="text-center py-8 text-gray-500">Backlog is empty.</div>}
          </div>
        )}
      </div>

      {viewingTask && !showForm && (
        <TaskDetailModal 
          task={viewingTask} 
          projectId={project.id} 
          onClose={() => setViewingTask(null)} 
          onUpdated={loadBacklog} 
          onEdit={() => {}}
          onDelete={() => {}}
        />
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 w-full max-w-lg shadow-xl relative">
            <h2 className="text-xl font-bold text-white mb-4">New Task</h2>
            <TaskForm 
              onSave={async (data) => {
                await taskApi.create(project.id, data);
                setShowForm(false);
                loadBacklog();
              }} 
              onCancel={() => setShowForm(false)} 
            />
          </div>
        </div>
      )}
    </div>
  );
}
