import os

base_dir = "c:/personal_projects/devflow/frontend"

files = {}

files["src/types/project.ts"] = """export enum ProjectStatus {
  PLANNING = "Planning",
  ACTIVE = "Active",
  ON_HOLD = "On Hold",
  COMPLETED = "Completed",
  ARCHIVED = "Archived"
}

export enum ProjectPriority {
  LOW = "Low",
  MEDIUM = "Medium",
  HIGH = "High",
  CRITICAL = "Critical"
}

export interface Project {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  description?: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  tech_stack: string[];
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedProjectResponse {
  items: Project[];
  page: int;
  page_size: int;
  total: int;
  total_pages: int;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  tech_stack: string[];
  start_date?: string;
  end_date?: string;
}

export interface ProjectUpdate extends Partial<ProjectCreate> {}
"""

files["src/lib/projectApi.ts"] = """import { api } from "./axios";
import { Project, ProjectCreate, ProjectUpdate, PaginatedProjectResponse, ProjectStatus, ProjectPriority } from "../types/project";

export const projectApi = {
  list: async (params?: { 
    page?: number; 
    page_size?: number; 
    search?: string; 
    status?: ProjectStatus; 
    priority?: ProjectPriority; 
    sort_by?: string; 
    sort_order?: string 
  }): Promise<PaginatedProjectResponse> => {
    const res = await api.get("/projects", { params });
    return res.data;
  },

  get: async (id: string): Promise<Project> => {
    const res = await api.get(`/projects/${id}`);
    return res.data;
  },

  create: async (data: ProjectCreate): Promise<Project> => {
    const res = await api.post("/projects", data);
    return res.data;
  },

  update: async (id: string, data: ProjectUpdate): Promise<Project> => {
    const res = await api.patch(`/projects/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`);
  }
};
"""

files["src/components/ProjectCard.tsx"] = """import React from "react";
import { Link } from "react-router-dom";
import { Project, ProjectStatus, ProjectPriority } from "../types/project";

const statusColors: Record<ProjectStatus, string> = {
  [ProjectStatus.PLANNING]: "bg-blue-900/50 text-blue-300 border-blue-800",
  [ProjectStatus.ACTIVE]: "bg-emerald-900/50 text-emerald-300 border-emerald-800",
  [ProjectStatus.ON_HOLD]: "bg-amber-900/50 text-amber-300 border-amber-800",
  [ProjectStatus.COMPLETED]: "bg-purple-900/50 text-purple-300 border-purple-800",
  [ProjectStatus.ARCHIVED]: "bg-gray-800 text-gray-400 border-gray-700",
};

const priorityColors: Record<ProjectPriority, string> = {
  [ProjectPriority.LOW]: "text-gray-400",
  [ProjectPriority.MEDIUM]: "text-blue-400",
  [ProjectPriority.HIGH]: "text-amber-400",
  [ProjectPriority.CRITICAL]: "text-red-400 font-semibold",
};

interface Props {
  project: Project;
  onDelete: (id: string) => void;
}

export function ProjectCard({ project, onDelete }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 flex flex-col hover:border-gray-700 transition-colors">
      <div className="flex justify-between items-start mb-2">
        <Link to={`/projects/${project.id}`} className="text-lg font-semibold text-white hover:text-blue-400 truncate">
          {project.name}
        </Link>
        <span className={`text-xs px-2 py-1 rounded-full border ${statusColors[project.status]}`}>
          {project.status}
        </span>
      </div>
      
      <p className="text-sm text-gray-400 line-clamp-2 mb-4 flex-1">
        {project.description || "No description provided."}
      </p>

      <div className="space-y-3 mt-auto">
        <div className="flex items-center text-xs justify-between">
          <span className="text-gray-500">Priority: <span className={priorityColors[project.priority]}>{project.priority}</span></span>
          <span className="text-gray-500">Updated: {new Date(project.updated_at || project.created_at).toLocaleDateString()}</span>
        </div>

        {project.tech_stack.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {project.tech_stack.slice(0, 3).map(tech => (
              <span key={tech} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded-md border border-gray-700">
                {tech}
              </span>
            ))}
            {project.tech_stack.length > 3 && (
              <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-md border border-gray-700">
                +{project.tech_stack.length - 3}
              </span>
            )}
          </div>
        )}

        <div className="flex items-center space-x-3 pt-3 border-t border-gray-800">
          <Link to={`/projects/${project.id}`} className="text-sm text-gray-300 hover:text-white transition-colors">Open</Link>
          <Link to={`/projects/${project.id}/edit`} className="text-sm text-gray-300 hover:text-white transition-colors">Edit</Link>
          <button 
            onClick={() => {
              if (window.confirm("Are you sure you want to delete this project?")) {
                onDelete(project.id);
              }
            }} 
            className="text-sm text-red-400 hover:text-red-300 transition-colors ml-auto"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
"""

for path, content in files.items():
    with open(os.path.join(base_dir, path), "w", encoding="utf-8") as f:
        f.write(content)

print("Frontend phase 2 part 1 generated.")
