import ProjectDiscussions from './ProjectDiscussions';
import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { projectApi } from "../lib/projectApi";
import { taskApi } from "../lib/taskApi";
import { Project } from "../types/project";
import { Task, TaskStats, TaskCreate, TaskStatus } from "../types/task";
import { Button } from "../components/ui/Button";
import { KanbanBoard } from "../components/KanbanBoard";
import { useRealtimeEvent } from '../hooks/useRealtime';
import { TaskForm } from "../components/TaskForm";
import { TaskDetailModal } from "../components/TaskDetailModal";
import { ProjectGitHub } from "../components/ProjectGitHub";
import { ProjectAI } from "../components/ProjectAI";
import { ProjectAnalytics } from "../components/ProjectAnalytics";
import { Sprints } from "../components/Sprints";
import { ActivityTimeline } from "../components/ActivityTimeline";
import { Backlog } from "../components/Backlog";
import { ProjectTimeTab } from "../components/ProjectTimeTab";
import { Roadmap } from "../components/Roadmap";
import Releases from "./Releases";
import Deployments from "./Deployments";
import InfrastructureAnalytics from "./infrastructure/InfrastructureAnalytics";
import PipelineRuns from "./PipelineRuns";

export default function ProjectDetails() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState<Project | null>(null);
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [activeTab, setActiveTab] = useState<"overview" | "tasks" | "github" | "ai" | "analytics" | "sprints" | "backlog" | "roadmap" | "activity" | "time" | "releases" | "deployments" | "pipelines" | "discussions" | "infrastructure">("overview");
  const [view, setView] = useState<"kanban" | "list">("kanban");
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [viewingTask, setViewingTask] = useState<Task | null>(null);

  const [sprintFilter, setSprintFilter] = useState<string>("all");
  const [availableSprints, setAvailableSprints] = useState<any[]>([]);

  useEffect(() => {
    loadData();
    // Also load sprints for filter
    if (projectId) {
      import("../lib/sprintApi").then(m => m.sprintApi.list(projectId)).then(setAvailableSprints).catch(console.error);
    }
  }, [projectId]);

  const loadData = async () => {
    try {
      const pData = await projectApi.get(projectId!);
      setProject(pData);
      
      const sData = await taskApi.getStats(projectId!);
      setStats(sData);
      
      await loadTasks(sprintFilter);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadTasks = async (filter: string) => {
    const params: any = { page_size: 100 };
    if (filter === "backlog") params.sprint_id = "null";
    else if (filter !== "all") params.sprint_id = filter;
    
    const tData = await taskApi.list(projectId!, params);
    setTasks(tData.items);
  };

  useEffect(() => {
    if (!loading && project) {
      loadTasks(sprintFilter);
    }
  }, [sprintFilter]);

  const handleTaskMove = async (taskId: string, newStatus: TaskStatus, newPosition: number) => {
    // Optimistic update
    setTasks(prev => prev.map((t: any) => t.id === taskId ? { ...t, status: newStatus, position: newPosition } : t));
    try {
      await taskApi.updateStatus(projectId!, taskId, newStatus, newPosition);
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
      setViewingTask(null);
    loadData();
  };

  const handleDeleteTask = async (id: string) => {
    if (window.confirm("Delete this task?")) {
      await taskApi.delete(projectId!, id);
      setShowForm(false);
      setEditingTask(null);
      setViewingTask(null);
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
          <Button onClick={() => { setEditingTask(null);
      setViewingTask(null); setShowForm(true); }}>Add Task</Button>
        </div>
      </div>
      
      <div className="flex gap-6 border-b border-gray-800 shrink-0 overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'tasks', label: 'Tasks' },
          { id: 'sprints', label: 'Sprints' },
          { id: 'backlog', label: 'Backlog' },
          { id: 'roadmap', label: 'Roadmap' },
            { id: 'releases', label: 'Releases' },
            { id: 'infrastructure', label: 'Infrastructure' },
            { id: 'deployments', label: 'Deployments' },
            { id: 'pipelines', label: 'Pipelines' },
          { id: 'activity', label: 'Activity' },
            { id: 'discussions', label: 'Discussions' },
          { id: 'github', label: 'GitHub' },
          { id: 'ai', label: 'AI Assistant' },
          { id: 'analytics', label: 'Analytics' },
            { id: 'time', label: 'Time' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`py-3 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${activeTab === tab.id ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 min-h-0 relative flex flex-col">
        {activeTab === 'overview' && (
          <div className="space-y-6">
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
            
            {/* Global dashboard current sprint widget will go here later */}
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="flex-1 flex flex-col h-full min-h-0">
            <div className="flex justify-between items-center border-b border-gray-800 shrink-0 mb-4 pb-2">
              <div className="flex gap-4">
                <button 
                  className={`px-4 py-2 font-medium text-sm transition-colors ${view === 'kanban' ? 'text-blue-400' : 'text-gray-500 hover:text-gray-300'}`}
                  onClick={() => setView('kanban')}
                >
                  Kanban Board
                </button>
                <button 
                  className={`px-4 py-2 font-medium text-sm transition-colors ${view === 'list' ? 'text-blue-400' : 'text-gray-500 hover:text-gray-300'}`}
                  onClick={() => setView('list')}
                >
                  List View
                </button>
              </div>
              <div>
                <select 
                  className="bg-gray-800 text-white text-sm rounded border border-gray-700 p-1.5 outline-none"
                  value={sprintFilter}
                  onChange={e => setSprintFilter(e.target.value)}
                >
                  <option value="all">All Tasks</option>
                  <option value="backlog">Backlog</option>
                  {availableSprints.map(s => (
                    <option key={s.id} value={s.id}>{s.name} ({s.status})</option>
                  ))}
                </select>
              </div>
            </div>

      <div className="flex-1 min-h-0 relative">
        {view === 'kanban' ? (
          <KanbanBoard tasks={tasks} onTaskMove={handleTaskMove} onTaskClick={(t: any) => setViewingTask(t)} />
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
                        <td className="px-4 py-3 font-medium text-white flex flex-col">
                            {t.task_key && <span className="text-[10px] text-gray-500 font-mono">{t.task_key}</span>}
                            <span>{t.title}</span>
                        </td>
                        <td className="px-4 py-3">{t.status.replace("_", " ")}</td>
                        <td className="px-4 py-3">{t.priority}</td>
                        <td className="px-4 py-3">{t.due_date ? new Date(t.due_date).toLocaleDateString() : '-'}</td>
                        <td className="px-4 py-3 text-right">
                          <button onClick={() => setViewingTask(t)} className="text-blue-400 hover:underline mr-3">View</button>
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
          </div>
        )}
        
        {activeTab === 'github' && <ProjectGitHub project={project} />}
        {activeTab === 'ai' && <ProjectAI project={project} />}
        {activeTab === 'analytics' && <ProjectAnalytics project={project} />}
          {activeTab === 'time' && <ProjectTimeTab projectId={project.id} />}
        {activeTab === 'sprints' && <Sprints project={project} />}
        {activeTab === 'backlog' && <Backlog project={project} />}
        {activeTab === 'roadmap' && <Roadmap project={project} />}
        {activeTab === 'releases' && <Releases />}
        {activeTab === 'deployments' && <Deployments />}
        {activeTab === 'pipelines' && <PipelineRuns />}
        {activeTab === 'discussions' && <ProjectDiscussions projectId={project.id} />}
        {activeTab === 'activity' && <div className="bg-gray-900 border border-gray-800 rounded-lg p-6"><ActivityTimeline projectId={project.id} /></div>}
      </div>
      
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

      {showForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 w-full max-w-lg shadow-xl relative">
            <h2 className="text-xl font-bold text-white mb-4">{editingTask ? 'Edit Task' : 'New Task'}</h2>
            <TaskForm 
              initialData={editingTask || undefined} 
              onSave={handleSaveTask} 
              onCancel={() => { setShowForm(false); setEditingTask(null);
      setViewingTask(null); }} 
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
