import React, { useState } from "react";
import { Task, TaskCreate, TaskStatus, TaskPriority } from "../types/task";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";

interface Props {
  initialData?: Task;
  onSave: (data: TaskCreate) => Promise<void>;
  onCancel: () => void;
}

export function TaskForm({ initialData, onSave, onCancel }: Props) {
  const [activeTab, setActiveTab] = useState<'basic'|'planning'|'org'|'structure'>('basic');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState<Partial<TaskCreate>>({
    title: initialData?.title || "",
    description: initialData?.description || "",
    status: initialData?.status || TaskStatus.TODO,
    priority: initialData?.priority || TaskPriority.MEDIUM,
    assignee_id: initialData?.assignee_id || "",
    due_date: initialData?.due_date ? initialData.due_date.substring(0, 10) : "",
    estimate_points: initialData?.estimate_points,
    estimate_hours: initialData?.estimate_hours,
    parent_id: initialData?.parent_id || "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title?.trim()) return setError("Title is required");
    
    setSaving(true);
    setError("");
    
    const payload = { ...formData };
    if (!payload.assignee_id) delete payload.assignee_id;
    if (!payload.parent_id) delete payload.parent_id;
    if (payload.due_date) {
        payload.due_date = new Date(payload.due_date).toISOString();
    } else {
        delete payload.due_date;
    }
    
    try {
      await onSave(payload as TaskCreate);
    } catch (err: any) {
      setError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || "Failed to save task.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[80vh]">
      <div className="flex space-x-4 border-b border-gray-800 pb-2 mb-4">
        {['basic', 'planning', 'org', 'structure'].map(tab => (
          <button 
            key={tab} 
            type="button"
            className={`capitalize pb-1 border-b-2 text-sm ${activeTab === tab ? 'border-blue-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
            onClick={() => setActiveTab(tab as any)}
          >
            {tab}
          </button>
        ))}
      </div>
      
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto pr-2 space-y-4">
        {error && <div className="p-3 text-sm text-red-500 bg-red-950/50 border border-red-900 rounded-md">{error}</div>}
        
        <div className={activeTab === 'basic' ? 'block' : 'hidden'}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Title *</label>
              <Input required name="title" value={formData.title} onChange={handleChange} autoFocus />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
              <textarea 
                name="description"
                className="flex min-h-[150px] w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                value={formData.description}
                onChange={handleChange}
              />
            </div>
          </div>
        </div>

        <div className={activeTab === 'planning' ? 'block' : 'hidden'}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
              <select name="status" className="h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100" value={formData.status} onChange={handleChange}>
                {Object.values(TaskStatus).map(s => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Priority</label>
              <select name="priority" className="h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100" value={formData.priority} onChange={handleChange}>
                {Object.values(TaskPriority).map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Assignee ID</label>
              <Input name="assignee_id" value={formData.assignee_id} onChange={handleChange} placeholder="Optional UUID" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Due Date</label>
              <Input type="date" name="due_date" value={formData.due_date} onChange={handleChange} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Estimate (Points)</label>
              <Input type="number" step="0.5" name="estimate_points" value={formData.estimate_points || ""} onChange={handleChange} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Estimate (Hours)</label>
              <Input type="number" step="0.5" name="estimate_hours" value={formData.estimate_hours || ""} onChange={handleChange} />
            </div>
          </div>
        </div>

        <div className={activeTab === 'org' ? 'block' : 'hidden'}>
           <p className="text-gray-400 text-sm">Labels and watchers management available in detail view after creation.</p>
        </div>

        <div className={activeTab === 'structure' ? 'block' : 'hidden'}>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Parent Task ID</label>
            <Input name="parent_id" value={formData.parent_id} onChange={handleChange} placeholder="Optional UUID" />
          </div>
          <p className="text-gray-400 text-sm mt-4">Dependencies can be configured in the detail view after creation.</p>
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-800 mt-6">
          <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
          <Button type="submit" isLoading={saving}>Save Task</Button>
        </div>
      </form>
    </div>
  );
}
