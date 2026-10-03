import React, { useState } from "react";
import { Task, TaskStatus } from "../types/task";
import { TaskCard } from "./TaskCard";

const columns = [
  { id: TaskStatus.TODO, title: "To Do" },
  { id: TaskStatus.IN_PROGRESS, title: "In Progress" },
  { id: TaskStatus.IN_REVIEW, title: "In Review" },
  { id: TaskStatus.DONE, title: "Done" },
];

interface Props {
  tasks: Task[];
  onTaskMove: (taskId: string, newStatus: TaskStatus, newPosition: number) => void;
  onTaskClick: (task: Task) => void;
}

export function KanbanBoard({ tasks, onTaskMove, onTaskClick }: Props) {
  const [dragOverCol, setDragOverCol] = useState<TaskStatus | null>(null);

  const handleDrop = (e: React.DragEvent, targetStatus: TaskStatus) => {
    e.preventDefault();
    setDragOverCol(null);
    const taskId = e.dataTransfer.getData("taskId");
    const sourceStatus = e.dataTransfer.getData("sourceStatus");
    
    if (!taskId) return;
    
    // Sort tasks in target col by position to figure out drop index based on mouse Y
    const colTasks = tasks.filter(t => t.status === targetStatus).sort((a, b) => a.position - b.position);
    
    // Simple approach: append at the end of the column if dropped on column
    let newPos = colTasks.length > 0 ? colTasks[colTasks.length - 1].position + 1.0 : 1.0;
    
    onTaskMove(taskId, targetStatus, newPos);
  };

  const handleDragOver = (e: React.DragEvent, status: TaskStatus) => {
    e.preventDefault();
    if (dragOverCol !== status) setDragOverCol(status);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOverCol(null);
  };

  return (
    <div className="flex gap-6 overflow-x-auto pb-4 h-full min-h-[500px]">
      {columns.map(col => {
        const colTasks = tasks.filter(t => t.status === col.id).sort((a, b) => a.position - b.position);
        
        return (
          <div 
            key={col.id} 
            className={`flex-1 min-w-[280px] max-w-[350px] bg-gray-900 rounded-lg flex flex-col border transition-colors ${
              dragOverCol === col.id ? "border-blue-500 bg-gray-800" : "border-gray-800"
            }`}
            onDrop={(e) => handleDrop(e, col.id)}
            onDragOver={(e) => handleDragOver(e, col.id)}
            onDragLeave={handleDragLeave}
          >
            <div className="p-3 border-b border-gray-800 flex items-center justify-between">
              <h3 className="font-medium text-gray-200">{col.title}</h3>
              <span className="bg-gray-800 text-gray-400 text-xs px-2 py-0.5 rounded-full">
                {colTasks.length}
              </span>
            </div>
            
            <div className="p-3 flex-1 overflow-y-auto space-y-3">
              {colTasks.map((task) => (
                <TaskCard key={task.id} task={task} onClick={onTaskClick} />
              ))}
              {colTasks.length === 0 && (
                <div className="h-full min-h-[100px] border-2 border-dashed border-gray-800 rounded flex items-center justify-center text-gray-500 text-sm pointer-events-none">
                  Drop here
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
