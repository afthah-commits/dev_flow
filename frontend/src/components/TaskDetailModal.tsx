import CommentThread from './CommentThread';
import React, { useState } from "react";
import { Task, TaskStatus } from "../types/task";
import { taskApi } from "../lib/taskApi";
import { Button } from "./ui/Button";
import { ActivityTimeline } from "./ActivityTimeline";

interface Props {
  task: Task;
  projectId: string;
  onClose: () => void;
  onUpdated: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export function TaskDetailModal({ task, projectId, onClose, onUpdated, onEdit, onDelete }: Props) {
  const [newChecklist, setNewChecklist] = useState("");
  
  const handleAddChecklist = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!newChecklist.trim()) return;
      await taskApi.addChecklist(projectId, task.id, newChecklist);
      setNewChecklist("");
      onUpdated();
  };
  
  const toggleChecklist = async (id: string, current: boolean) => {
      await taskApi.updateChecklist(projectId, task.id, id, !current);
      onUpdated();
  };

  const deleteChecklist = async (id: string) => {
      await taskApi.deleteChecklist(projectId, task.id, id);
      onUpdated();
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-gray-900 border border-gray-800 rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden relative">
        <div className="flex justify-between items-start p-6 border-b border-gray-800 shrink-0">
            <div>
                <div className="flex items-center gap-3 mb-1">
                    {task.task_key && <span className="text-sm font-mono text-gray-400">{task.task_key}</span>}
                    <span className={`px-2 py-0.5 rounded text-xs border ${
                        task.status === TaskStatus.DONE ? 'bg-emerald-900/30 text-emerald-400 border-emerald-800' : 
                        task.status === TaskStatus.IN_PROGRESS ? 'bg-blue-900/30 text-blue-400 border-blue-800' : 
                        'bg-gray-800 text-gray-300 border-gray-700'
                    }`}>
                        {task.status.replace("_", " ")}
                    </span>
                    {task.is_blocked && (
                        <span className="px-2 py-0.5 rounded text-xs border bg-red-900/30 text-red-400 border-red-800">
                            BLOCKED
                        </span>
                    )}
                </div>
                <h2 className="text-2xl font-bold text-white">{task.title}</h2>
            </div>
            <div className="flex gap-2">
                <button onClick={() => {
                    window.dispatchEvent(new CustomEvent('start_task_timer', { detail: { taskId: task.id, projectId: task.project_id || projectId, title: task.title } }));
                  }} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center gap-2 text-sm">
                    ? Start Timer
                  </button>
                  <Button variant="outline" onClick={onEdit}>Edit</Button>
                <Button variant="outline" onClick={onDelete} className="text-red-400 hover:text-red-300">Delete</Button>
                <button onClick={onClose} className="text-gray-500 hover:text-white ml-2">✕</button>
            </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 grid grid-cols-3 gap-6">
            <div className="col-span-2 space-y-8">
                <div>
                    <h3 className="text-sm font-medium text-gray-400 mb-2">Description</h3>
                    <div className="text-gray-200 whitespace-pre-wrap text-sm leading-relaxed">
                        {task.description || <span className="text-gray-600 italic">No description provided.</span>}
                    </div>
                </div>

                <div>
                    <h3 className="text-sm font-medium text-gray-400 mb-2">Checklist</h3>
                    <div className="space-y-2">
                        {task.checklists?.map(item => (
                            <div key={item.id} className="flex items-center justify-between group">
                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input 
                                        type="checkbox" 
                                        checked={item.completed} 
                                        onChange={() => toggleChecklist(item.id, item.completed)}
                                        className="rounded border-gray-600 bg-gray-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900" 
                                    />
                                    <span className={`text-sm ${item.completed ? 'text-gray-500 line-through' : 'text-gray-200'}`}>{item.text}</span>
                                </label>
                                <button onClick={() => deleteChecklist(item.id)} className="text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">✕</button>
                            </div>
                        ))}
                    </div>
                    <form onSubmit={handleAddChecklist} className="mt-3 flex gap-2">
                        <input 
                            type="text" 
                            value={newChecklist} 
                            onChange={e => setNewChecklist(e.target.value)} 
                            placeholder="Add checklist item..."
                            className="flex-1 rounded-md border border-gray-700 bg-gray-800 px-3 py-1 text-sm text-white" 
                        />
                        <Button type="submit" variant="outline">Add</Button>
                    </form>
                </div>
                
                {task.subtasks && task.subtasks.length > 0 && (
                <div>
                    <h3 className="text-sm font-medium text-gray-400 mb-2">Subtasks</h3>
                    <div className="border border-gray-800 rounded-md overflow-hidden bg-gray-800/30">
                        {task.subtasks.map(st => (
                            <div key={st.id} className="p-3 border-b border-gray-800 last:border-0 flex items-center justify-between">
                                <span className="text-sm text-gray-300">{st.title}</span>
                                <span className="text-xs text-gray-500">{st.status}</span>
                            </div>
                        ))}
                    </div>
                </div>
                )}
            </div>

            <div className="mt-8 pt-8 border-t border-gray-800"><CommentThread entityType="TASK" entityId={task.id} /></div>
            <div className="col-span-1 space-y-6">
                <div className="bg-gray-800/50 p-4 rounded-md border border-gray-800 space-y-4 text-sm">
                    <div>
                        <span className="text-gray-500 block mb-1">Priority</span>
                        <span className="text-white font-medium">{task.priority}</span>
                    </div>
                    <div>
                        <span className="text-gray-500 block mb-1">Assignee</span>
                        <span className="text-gray-300">{task.assignee_id ? "Assigned" : "Unassigned"}</span>
                    </div>
                    <div>
                        <span className="text-gray-500 block mb-1">Due Date</span>
                        <span className="text-gray-300">{task.due_date ? new Date(task.due_date).toLocaleDateString() : "None"}</span>
                    </div>
                    <div>
                        <span className="text-gray-500 block mb-1">Estimate (Points)</span>
                        <span className="text-gray-300">{task.estimate_points || "-"}</span>
                    </div>
                    <div>
                        <span className="text-gray-500 block mb-1">Estimate (Hours)</span>
                        <span className="text-gray-300">{task.estimate_hours || "-"} h</span>
                    </div>
                    <div>
                        <span className="text-gray-500 block mb-1">Actual (Hours)</span>
                        <span className="text-gray-300">{task.actual_hours || "-"} h</span>
                    </div>
                </div>
                
                {(task.labels_rel?.length || task.labels?.length) ? (
                <div>
                    <h3 className="text-sm font-medium text-gray-400 mb-2">Labels</h3>
                    <div className="flex flex-wrap gap-2">
                        {task.labels_rel?.map(l => (
                            <span key={l.id} className="text-xs px-2 py-1 rounded text-gray-300" style={{backgroundColor: l.color + '40', border: `1px solid ${l.color}80`}}>
                                {l.name}
                            </span>
                        ))}
                        {!task.labels_rel?.length && task.labels?.map(l => (
                            <span key={l} className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">
                                {l}
                            </span>
                        ))}
                    </div>
                </div>
                ) : null}
            </div>
            
            <div className="col-span-3 mt-4 pt-6 border-t border-gray-800">
                <h3 className="text-lg font-bold text-white mb-4">Activity</h3>
                <ActivityTimeline projectId={projectId} taskId={task.id} />
            </div>
        </div>
      </div>
    </div>
  );
}
