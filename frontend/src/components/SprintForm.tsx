import React, { useState } from "react";
import { sprintApi } from "../lib/sprintApi";
import { Button } from "./ui/Button";

interface SprintFormProps {
  projectId: string;
  initialData?: any;
  onClose: () => void;
  onSuccess: () => void;
}

export function SprintForm({ projectId, initialData, onClose, onSuccess }: SprintFormProps) {
  const [formData, setFormData] = useState({
    name: initialData?.name || "",
    goal: initialData?.goal || "",
    description: initialData?.description || "",
    start_date: initialData?.start_date ? new Date(initialData.start_date).toISOString().slice(0, 16) : "",
    end_date: initialData?.end_date ? new Date(initialData.end_date).toISOString().slice(0, 16) : "",
    capacity: initialData?.capacity || ""
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...formData,
        start_date: formData.start_date ? new Date(formData.start_date).toISOString() : null,
        end_date: formData.end_date ? new Date(formData.end_date).toISOString() : null,
        capacity: formData.capacity ? parseFloat(formData.capacity) : null
      };
      
      if (initialData) {
        await sprintApi.update(projectId, initialData.id, payload);
      } else {
        await sprintApi.create(projectId, payload);
      }
      onSuccess();
    } catch (err) {
      console.error(err);
      alert("Failed to save sprint");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 w-full max-w-lg shadow-xl relative">
        <h2 className="text-xl font-bold text-white mb-4">{initialData ? 'Edit Sprint' : 'New Sprint'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
            <input 
              required
              type="text" 
              className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white focus:border-blue-500 outline-none"
              value={formData.name}
              onChange={e => setFormData({...formData, name: e.target.value})}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Goal</label>
            <textarea 
              className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white focus:border-blue-500 outline-none h-20"
              value={formData.goal}
              onChange={e => setFormData({...formData, goal: e.target.value})}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Start Date</label>
              <input 
                type="datetime-local" 
                className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white focus:border-blue-500 outline-none"
                value={formData.start_date}
                onChange={e => setFormData({...formData, start_date: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">End Date</label>
              <input 
                type="datetime-local" 
                className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white focus:border-blue-500 outline-none"
                value={formData.end_date}
                onChange={e => setFormData({...formData, end_date: e.target.value})}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Capacity (points)</label>
            <input 
              type="number" 
              step="0.5"
              className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white focus:border-blue-500 outline-none"
              value={formData.capacity}
              onChange={e => setFormData({...formData, capacity: e.target.value})}
            />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={loading}>{loading ? 'Saving...' : 'Save'}</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
