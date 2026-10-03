import React, { useState, useEffect } from "react";
import { sprintApi } from "../lib/sprintApi";
import { backlogApi } from "../lib/backlogApi";
import { taskApi } from "../lib/taskApi";
import { Button } from "./ui/Button";
import { TaskCard } from "./TaskCard";

export function SprintPlanning({ projectId, sprint, onUpdate }: { projectId: string, sprint: any, onUpdate: () => void }) {
  const [backlogTasks, setBacklogTasks] = useState<any[]>([]);
  const [sprintTasks, setSprintTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBacklog, setSelectedBacklog] = useState<Set<string>>(new Set());
  const [selectedSprint, setSelectedSprint] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadData();
  }, [sprint.id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [bData, sData] = await Promise.all([
        backlogApi.get(projectId, { page_size: 100 }),
        taskApi.list(projectId, { sprint_id: sprint.id, page_size: 100 })
      ]);
      setBacklogTasks(bData.items);
      setSprintTasks(sData.items);
      setSelectedBacklog(new Set());
      setSelectedSprint(new Set());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleMoveToSprint = async (taskIds: string[]) => {
    try {
      await sprintApi.addTasks(projectId, sprint.id, taskIds);
      loadData();
      onUpdate();
    } catch (e) {
      alert("Failed to move tasks");
    }
  };

  const handleMoveToBacklog = async (taskIds: string[]) => {
    try {
      await Promise.all(taskIds.map(id => sprintApi.removeTask(projectId, sprint.id, id)));
      loadData();
      onUpdate();
    } catch (e) {
      alert("Failed to move tasks");
    }
  };

  const toggleSelection = (id: string, isBacklog: boolean) => {
    if (isBacklog) {
      const newSet = new Set(selectedBacklog);
      if (newSet.has(id)) newSet.delete(id);
      else newSet.add(id);
      setSelectedBacklog(newSet);
    } else {
      const newSet = new Set(selectedSprint);
      if (newSet.has(id)) newSet.delete(id);
      else newSet.add(id);
      setSelectedSprint(newSet);
    }
  };

  if (loading) return <div>Loading planning view...</div>;

  return (
    <div className="flex h-full gap-6">
      <div className="flex-1 flex flex-col bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-800/50">
          <h3 className="font-bold">Product Backlog ({backlogTasks.length})</h3>
          <Button 
            disabled={selectedBacklog.size === 0} 
            onClick={() => handleMoveToSprint(Array.from(selectedBacklog))}
            className="text-xs py-1"
          >
            Move to Sprint &rarr;
          </Button>
        </div>
        <div className="flex-1 overflow-auto p-4 space-y-2">
          {backlogTasks.map(t => (
            <div key={t.id} className="flex items-start gap-3">
              <input 
                type="checkbox" 
                className="mt-2"
                checked={selectedBacklog.has(t.id)} 
                onChange={() => toggleSelection(t.id, true)} 
              />
              <div className="flex-1">
                <TaskCard task={t} onClick={() => {}} />
              </div>
            </div>
          ))}
          {backlogTasks.length === 0 && <div className="text-gray-500 text-center py-4 text-sm">Backlog is empty</div>}
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-800/50">
          <Button 
            disabled={selectedSprint.size === 0} 
            variant="outline"
            onClick={() => handleMoveToBacklog(Array.from(selectedSprint))}
            className="text-xs py-1"
          >
            &larr; Remove
          </Button>
          <h3 className="font-bold">{sprint.name} ({sprintTasks.length})</h3>
        </div>
        <div className="flex-1 overflow-auto p-4 space-y-2">
          {sprintTasks.map(t => (
            <div key={t.id} className="flex items-start gap-3">
              <div className="flex-1">
                <TaskCard task={t} onClick={() => {}} />
              </div>
              <input 
                type="checkbox" 
                className="mt-2"
                checked={selectedSprint.has(t.id)} 
                onChange={() => toggleSelection(t.id, false)} 
              />
            </div>
          ))}
          {sprintTasks.length === 0 && <div className="text-gray-500 text-center py-4 text-sm">Sprint is empty</div>}
        </div>
      </div>
    </div>
  );
}
