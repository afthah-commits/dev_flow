import os

base_dir = "c:/personal_projects/devflow/frontend"
files = {}

files["src/components/TaskCard.tsx"] = """import React from "react";
import { Task, TaskPriority, TaskStatus } from "../types/task";

const priorityColors: Record<TaskPriority, string> = {
  [TaskPriority.LOW]: "text-gray-400 bg-gray-800/50",
  [TaskPriority.MEDIUM]: "text-blue-400 bg-blue-900/30",
  [TaskPriority.HIGH]: "text-amber-400 bg-amber-900/30",
  [TaskPriority.CRITICAL]: "text-red-400 bg-red-900/30 font-semibold",
};

interface Props {
  task: Task;
  onClick: (task: Task) => void;
}

export function TaskCard({ task, onClick }: Props) {
  return (
    <div 
      onClick={() => onClick(task)}
      className="bg-gray-800 border border-gray-700 rounded-md p-3 cursor-pointer hover:border-gray-500 transition-colors shadow-sm"
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData("taskId", task.id);
        e.dataTransfer.setData("sourceStatus", task.status);
      }}
    >
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-sm font-medium text-white line-clamp-2">{task.title}</h4>
      </div>
      
      {task.labels && task.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {task.labels.slice(0, 3).map((label: string) => (
            <span key={label} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-300">
              {label}
            </span>
          ))}
          {task.labels.length > 3 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-400">
              +{task.labels.length - 3}
            </span>
          )}
        </div>
      )}
      
      <div className="flex items-center justify-between mt-3 text-xs">
        <span className={`px-1.5 py-0.5 rounded-sm ${priorityColors[task.priority]}`}>
          {task.priority}
        </span>
        {task.due_date && (
          <span className={`text-gray-500 ${new Date(task.due_date) < new Date() && task.status !== TaskStatus.DONE ? 'text-red-400' : ''}`}>
            {new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
          </span>
        )}
      </div>
    </div>
  );
}
"""

files["src/components/KanbanBoard.tsx"] = """import React, { useState } from "react";
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
  onTaskMove: (taskId: string, newStatus: TaskStatus) => void;
  onTaskClick: (task: Task) => void;
}

export function KanbanBoard({ tasks, onTaskMove, onTaskClick }: Props) {
  const [dragOverCol, setDragOverCol] = useState<TaskStatus | null>(null);

  const handleDrop = (e: React.DragEvent, targetStatus: TaskStatus) => {
    e.preventDefault();
    setDragOverCol(null);
    const taskId = e.dataTransfer.getData("taskId");
    const sourceStatus = e.dataTransfer.getData("sourceStatus");
    if (taskId && sourceStatus !== targetStatus) {
      onTaskMove(taskId, targetStatus);
    }
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
        const colTasks = tasks.filter((t: any) => t.status === col.id);
        
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
              {colTasks.map((task: any) => (
                <TaskCard key={task.id} task={task} onClick={onTaskClick} />
              ))}
              {colTasks.length === 0 && (
                <div className="h-full min-h-[100px] border-2 border-dashed border-gray-800 rounded flex items-center justify-center text-gray-500 text-sm">
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
"""

for path, content in files.items():
    with open(os.path.join(base_dir, path), "w", encoding="utf-8") as f:
        f.write(content)

print("Frontend Phase 3 part 2 generated.")
