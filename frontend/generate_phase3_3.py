import os

base_dir = "c:/personal_projects/devflow/frontend"
files = {}

files["src/components/TaskForm.tsx"] = """import React, { useState, useEffect } from "react";
import { Task, TaskCreate, TaskStatus, TaskPriority } from "../types/task";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";

interface Props {
  initialData?: Task;
  onSave: (data: TaskCreate) => Promise<void>;
  onCancel: () => void;
}

export function TaskForm({ initialData, onSave, onCancel }: Props) {
  const [title, setTitle] = useState(initialData?.title || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [status, setStatus] = useState<TaskStatus>(initialData?.status || TaskStatus.TODO);
  const [priority, setPriority] = useState<TaskPriority>(initialData?.priority || TaskPriority.MEDIUM);
  const [labels, setLabels] = useState(initialData?.labels?.join(", ") || "");
  const [dueDate, setDueDate] = useState(initialData?.due_date ? initialData.due_date.substring(0, 10) : "");
  
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return setError("Title is required");
    
    setSaving(true);
    setError("");
    
    const parsedLabels = labels.split(",").map((s: string) => s.trim()).filter((s: string) => s.length > 0);
    const data: TaskCreate = {
      title,
      description,
      status,
      priority,
      labels: parsedLabels,
      due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
    };
    
    try {
      await onSave(data);
    } catch (err: any) {
      setError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || "Failed to save task.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <div className="p-3 text-sm text-red-500 bg-red-950/50 border border-red-900 rounded-md">{error}</div>}
      
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Title *</label>
        <Input required value={title} onChange={e => setTitle(e.target.value)} autoFocus />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
        <textarea 
          className="flex min-h-[80px] w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          value={description}
          onChange={e => setDescription(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
          <select 
            className="h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100"
            value={status}
            onChange={e => setStatus(e.target.value as TaskStatus)}
          >
            {Object.values(TaskStatus).map(s => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Priority</label>
          <select 
            className="h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100"
            value={priority}
            onChange={e => setPriority(e.target.value as TaskPriority)}
          >
            {Object.values(TaskPriority).map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Due Date</label>
          <Input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Labels</label>
          <Input placeholder="Bug, Feature, etc." value={labels} onChange={e => setLabels(e.target.value)} />
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-800">
        <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
        <Button type="submit" isLoading={saving}>Save Task</Button>
      </div>
    </form>
  );
}
"""

files["src/pages/ProjectDetails.tsx"] = """import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { projectApi } from "../lib/projectApi";
import { taskApi } from "../lib/taskApi";
import { Project } from "../types/project";
import { Task, TaskStats, TaskCreate, TaskStatus } from "../types/task";
import { Button } from "../components/ui/Button";
import { KanbanBoard } from "../components/KanbanBoard";
import { TaskForm } from "../components/TaskForm";

export default function ProjectDetails() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState<Project | null>(null);
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [view, setView] = useState<"kanban" | "list">("kanban");
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  useEffect(() => {
    loadData();
  }, [projectId]);

  const loadData = async () => {
    try {
      const pData = await projectApi.get(projectId!);
      setProject(pData);
      
      const sData = await taskApi.getStats(projectId!);
      setStats(sData);
      
      // Load all tasks for Kanban
      const tData = await taskApi.list(projectId!, { page_size: 100 });
      setTasks(tData.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskMove = async (taskId: string, newStatus: TaskStatus) => {
    // Optimistic update
    setTasks(prev => prev.map((t: any) => t.id === taskId ? { ...t, status: newStatus } : t));
    try {
      await taskApi.updateStatus(projectId!, taskId, newStatus);
      // reload stats
      const sData = await taskApi.getStats(projectId!);
      setStats(sData);
    } catch (err) {
      alert("Failed to move task");
      loadData(); // revert
    }
  };

  const handleSaveTask = async (data: TaskCreate) => {
    if (editingTask) {
      await taskApi.update(projectId!, editingTask.id, data);
    } else {
      await taskApi.create(projectId!, data);
    }
    setShowForm(false);
    setEditingTask(null);
    loadData();
  };

  const handleDeleteTask = async (id: string) => {
    if (window.confirm("Delete this task?")) {
      await taskApi.delete(projectId!, id);
      setShowForm(false);
      setEditingTask(null);
      loadData();
    }
  };

  if (loading) return <div className="text-gray-400">Loading...</div>;
  if (!project) return <div className="text-red-400">Project not found</div>;

  return (
    <div className="max-w-[1600px] mx-auto space-y-6 h-[calc(100vh-100px)] flex flex-col">
      <div className="flex items-start justify-between shrink-0">
        <div>
          <Link to="/projects" className="text-sm text-blue-500 hover:text-blue-400 mb-2 inline-block">&larr; Back to projects</Link>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            {project.name}
            <span className="text-xs px-2 py-1 rounded-full border bg-gray-800 text-gray-300 border-gray-700 font-normal">
              {project.status}
            </span>
          </h1>
          <p className="mt-1 text-gray-400 text-sm max-w-2xl">{project.description}</p>
        </div>
        <div className="flex space-x-3">
          <Link to={`/projects/${project.id}/edit`}>
            <Button variant="outline">Edit Project</Button>
          </Link>
          <Button onClick={() => { setEditingTask(null); setShowForm(true); }}>Add Task</Button>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 shrink-0">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
            <span className="text-xs text-gray-500 block">Total</span>
            <span className="text-xl font-bold text-white">{stats.total}</span>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
            <span className="text-xs text-gray-500 block">To Do</span>
            <span className="text-xl font-bold text-gray-300">{stats.todo}</span>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
            <span className="text-xs text-gray-500 block">In Progress</span>
            <span className="text-xl font-bold text-blue-400">{stats.in_progress}</span>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
            <span className="text-xs text-gray-500 block">In Review</span>
            <span className="text-xl font-bold text-amber-400">{stats.in_review}</span>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
            <span className="text-xs text-gray-500 block">Done</span>
            <span className="text-xl font-bold text-emerald-400">{stats.done}</span>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
            <span className="text-xs text-gray-500 block">Overdue</span>
            <span className="text-xl font-bold text-red-400">{stats.overdue}</span>
          </div>
        </div>
      )}

      <div className="flex gap-4 border-b border-gray-800 shrink-0">
        <button 
          className={`px-4 py-2 border-b-2 font-medium text-sm transition-colors ${view === 'kanban' ? 'border-blue-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
          onClick={() => setView('kanban')}
        >
          Kanban Board
        </button>
        <button 
          className={`px-4 py-2 border-b-2 font-medium text-sm transition-colors ${view === 'list' ? 'border-blue-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
          onClick={() => setView('list')}
        >
          List View
        </button>
      </div>

      <div className="flex-1 min-h-0 relative">
        {view === 'kanban' ? (
          <KanbanBoard tasks={tasks} onTaskMove={handleTaskMove} onTaskClick={(t: any) => { setEditingTask(t); setShowForm(true); }} />
        ) : (
          <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden h-full flex flex-col">
            <div className="overflow-auto flex-1">
              <table className="w-full text-left text-sm text-gray-300">
                <thead className="bg-gray-800 text-xs uppercase text-gray-400 sticky top-0">
                  <tr>
                    <th className="px-4 py-3">Title</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Priority</th>
                    <th className="px-4 py-3">Due Date</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.length === 0 ? (
                    <tr><td colSpan={5} className="text-center py-8 text-gray-500">No tasks found.</td></tr>
                  ) : (
                    tasks.map((t: any) => (
                      <tr key={t.id} className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
                        <td className="px-4 py-3 font-medium text-white">{t.title}</td>
                        <td className="px-4 py-3">{t.status.replace("_", " ")}</td>
                        <td className="px-4 py-3">{t.priority}</td>
                        <td className="px-4 py-3">{t.due_date ? new Date(t.due_date).toLocaleDateString() : '-'}</td>
                        <td className="px-4 py-3 text-right">
                          <button onClick={() => { setEditingTask(t); setShowForm(true); }} className="text-blue-400 hover:underline mr-3">Edit</button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 w-full max-w-lg shadow-xl relative">
            <h2 className="text-xl font-bold text-white mb-4">{editingTask ? 'Edit Task' : 'New Task'}</h2>
            <TaskForm 
              initialData={editingTask || undefined} 
              onSave={handleSaveTask} 
              onCancel={() => { setShowForm(false); setEditingTask(null); }} 
            />
            {editingTask && (
              <button 
                onClick={() => handleDeleteTask(editingTask.id)}
                className="absolute top-6 right-6 text-sm text-red-400 hover:text-red-300"
              >
                Delete
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
"""

for path, content in files.items():
    with open(os.path.join(base_dir, path), "w", encoding="utf-8") as f:
        f.write(content)

print("Frontend Phase 3 part 3 generated.")
