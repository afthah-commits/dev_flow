import React, { useState, useEffect } from "react";
import { Project } from "../types/project";
import { sprintApi } from "../lib/sprintApi";
import { Button } from "./ui/Button";
import { SprintForm } from "./SprintForm";
import { SprintDetails } from "./SprintDetails";

export function Sprints({ project }: { project: Project }) {
  const [sprints, setSprints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedSprintId, setSelectedSprintId] = useState<string | null>(null);

  useEffect(() => {
    loadSprints();
  }, [project.id]);

  const loadSprints = async () => {
    setLoading(true);
    try {
      const data = await sprintApi.list(project.id);
      setSprints(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (selectedSprintId) {
    return (
      <SprintDetails 
        projectId={project.id} 
        sprintId={selectedSprintId} 
        onBack={() => { setSelectedSprintId(null); loadSprints(); }} 
      />
    );
  }

  return (
    <div className="flex-1 overflow-auto h-full p-1 text-gray-200 space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Sprints</h2>
        <Button onClick={() => setShowForm(true)}>Create Sprint</Button>
      </div>

      {loading ? (
        <div>Loading sprints...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sprints.map(sprint => (
            <div 
              key={sprint.id} 
              className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col cursor-pointer hover:border-gray-600 transition-colors"
              onClick={() => setSelectedSprintId(sprint.id)}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="font-mono text-xs text-gray-400">{sprint.key}</span>
                <span className={`text-xs px-2 py-1 rounded-full border ${sprint.status === 'ACTIVE' ? 'bg-blue-900/50 text-blue-300 border-blue-800' : 'bg-gray-800 text-gray-300 border-gray-700'}`}>
                  {sprint.status}
                </span>
              </div>
              <h3 className="font-bold text-lg mb-1">{sprint.name}</h3>
              {sprint.goal && <p className="text-sm text-gray-400 mb-3 flex-1 line-clamp-2">{sprint.goal}</p>}
              <div className="text-xs text-gray-500 mt-auto pt-3 border-t border-gray-800 flex justify-between">
                <span>{sprint.start_date ? new Date(sprint.start_date).toLocaleDateString() : 'No start date'}</span>
                <span>{sprint.end_date ? new Date(sprint.end_date).toLocaleDateString() : 'No end date'}</span>
              </div>
            </div>
          ))}
          {sprints.length === 0 && (
            <div className="col-span-full text-center py-10 text-gray-500">
              No sprints found. Create one to get started.
            </div>
          )}
        </div>
      )}

      {showForm && (
        <SprintForm 
          projectId={project.id}
          onClose={() => setShowForm(false)}
          onSuccess={() => { setShowForm(false); loadSprints(); }}
        />
      )}
    </div>
  );
}
