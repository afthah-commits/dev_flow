import React from "react";
import { Task, TaskPriority, TaskStatus, Label } from "../types/task";

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
      className={`bg-gray-800 border ${task.is_blocked ? 'border-red-900/50' : 'border-gray-700'} rounded-md p-3 cursor-pointer hover:border-gray-500 transition-colors shadow-sm relative overflow-hidden`}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData("taskId", task.id);
        e.dataTransfer.setData("sourceStatus", task.status);
      }}
    >
      {task.is_blocked && (
        <div className="absolute top-0 right-0 border-t-16 border-r-16 border-t-red-900 border-r-transparent w-4 h-4"></div>
      )}
      <div className="flex justify-between items-start mb-2 gap-2">
        <div className="flex flex-col">
           {task.task_key && <span className="text-[10px] text-gray-500 font-mono mb-0.5">{task.task_key}</span>}
           <h4 className="text-sm font-medium text-white line-clamp-2 leading-tight">{task.title}</h4>
        </div>
      </div>
      
      {((task.labels_rel && task.labels_rel.length > 0) || (task.labels && task.labels.length > 0)) && (
        <div className="flex flex-wrap gap-1 mb-3">
          {task.labels_rel?.slice(0, 3).map((l: Label) => (
            <span key={l.id} className="text-[10px] px-1.5 py-0.5 rounded text-gray-300" style={{backgroundColor: l.color + '40', border: `1px solid ${l.color}80`}}>
              {l.name}
            </span>
          ))}
          {(!task.labels_rel || task.labels_rel.length === 0) && task.labels?.slice(0, 3).map((label: string) => (
            <span key={label} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-300">
              {label}
            </span>
          ))}
        </div>
      )}
      
      <div className="flex items-center justify-between mt-3 text-xs">
        <div className="flex gap-2 items-center">
            <span className={`px-1.5 py-0.5 rounded-sm ${priorityColors[task.priority]}`}>
            {task.priority}
            </span>
            {task.estimate_points && <span className="text-gray-500 font-mono text-[10px]">{task.estimate_points} pts</span>}
        </div>
        
        <div className="flex gap-2">
            {task.subtasks && task.subtasks.length > 0 && (
                <span className="text-gray-500 text-[10px] flex items-center gap-1">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 5v4M9 15v4M15 5v4M15 15v4M5 9h14M5 15h14"/></svg>
                    {task.subtasks.filter(t => t.status === TaskStatus.DONE).length}/{task.subtasks.length}
                </span>
            )}
            {task.due_date && (
            <span className={`text-gray-500 ${new Date(task.due_date) < new Date() && task.status !== TaskStatus.DONE ? 'text-red-400' : ''}`}>
                {new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
            </span>
            )}
        </div>
      </div>
    </div>
  );
}
