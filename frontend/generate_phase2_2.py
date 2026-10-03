import os

base_dir = "c:/personal_projects/devflow/frontend"
files = {}

files["src/pages/Dashboard.tsx"] = """import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { projectApi } from "../lib/projectApi";
import { Project, ProjectStatus } from "../types/project";
import { ProjectCard } from "../components/ProjectCard";

export default function Dashboard() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 4, sort_by: "updated_at", sort_order: "desc" });
      setProjects(res.items);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await projectApi.delete(id);
      loadProjects();
    } catch (error) {
      console.error(error);
      alert("Failed to delete project");
    }
  };

  const total = projects.length; // Approximate for recent
  const active = projects.filter(p => p.status === ProjectStatus.ACTIVE).length;
  const completed = projects.filter(p => p.status === ProjectStatus.COMPLETED).length;
  const onHold = projects.filter(p => p.status === ProjectStatus.ON_HOLD).length;

  if (loading) {
    return <div className="text-gray-400">Loading dashboard...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Welcome back, {user?.name}</h1>
          <p className="mt-1 text-gray-400">Here's what's happening with your projects today.</p>
        </div>
        <Link 
          to="/projects/new" 
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
        >
          Create Project
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[ 
          { label: "Total Recent", value: total, color: "text-blue-400" },
          { label: "Active", value: active, color: "text-emerald-400" },
          { label: "Completed", value: completed, color: "text-purple-400" },
          { label: "On Hold", value: onHold, color: "text-amber-400" }
        ].map(stat => (
          <div key={stat.label} className="bg-gray-900 border border-gray-800 rounded-lg p-6 flex flex-col">
            <span className="text-sm font-medium text-gray-400">{stat.label}</span>
            <span className={`text-3xl font-bold mt-2 ${stat.color}`}>{stat.value}</span>
          </div>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">Recent Projects</h2>
          <Link to="/projects" className="text-sm text-blue-500 hover:text-blue-400 transition-colors">
            View all projects &rarr;
          </Link>
        </div>
        
        {projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map(p => (
              <ProjectCard key={p.id} project={p} onDelete={handleDelete} />
            ))}
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
            <h3 className="text-lg font-medium text-white mb-2">No projects yet</h3>
            <p className="text-gray-400 mb-6">Create your first project to get started with DevFlow.</p>
            <Link 
              to="/projects/new" 
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors inline-block"
            >
              Create Project
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
"""

files["src/pages/Projects.tsx"] = """import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { projectApi } from "../lib/projectApi";
import { Project, ProjectStatus, ProjectPriority, PaginatedProjectResponse } from "../types/project";
import { ProjectCard } from "../components/ProjectCard";
import { Input } from "../components/ui/Input";

export default function Projects() {
  const [data, setData] = useState<PaginatedProjectResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ProjectStatus | "">("");
  const [priority, setPriority] = useState<ProjectPriority | "">("");
  const [sortBy, setSortBy] = useState("updated_at");

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      loadProjects();
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [search, status, priority, sortBy]);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const res = await projectApi.list({ 
        page: 1, 
        page_size: 100, // simplified for now
        search: search || undefined,
        status: status ? (status as ProjectStatus) : undefined,
        priority: priority ? (priority as ProjectPriority) : undefined,
        sort_by: sortBy === "name" ? "name" : "updated_at",
        sort_order: sortBy === "name" ? "asc" : "desc"
      });
      setData(res);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await projectApi.delete(id);
      loadProjects();
    } catch (error) {
      console.error(error);
      alert("Failed to delete project");
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Projects</h1>
          <p className="mt-1 text-gray-400">Manage your workspace projects.</p>
        </div>
        <Link to="/projects/new" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors">
          Create Project
        </Link>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col md:flex-row gap-4 items-center">
        <div className="flex-1 w-full">
          <Input 
            placeholder="Search projects..." 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
            className="w-full"
          />
        </div>
        <select 
          className="h-10 rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100 w-full md:w-auto"
          value={status}
          onChange={(e) => setStatus(e.target.value as any)}
        >
          <option value="">All Statuses</option>
          {Object.values(ProjectStatus).map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select 
          className="h-10 rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100 w-full md:w-auto"
          value={priority}
          onChange={(e) => setPriority(e.target.value as any)}
        >
          <option value="">All Priorities</option>
          {Object.values(ProjectPriority).map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <select 
          className="h-10 rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100 w-full md:w-auto"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
        >
          <option value="updated_at">Recently Updated</option>
          <option value="name">Name (A-Z)</option>
        </select>
      </div>

      {loading && !data ? (
        <div className="text-gray-400">Loading projects...</div>
      ) : data?.items.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
          <h3 className="text-lg font-medium text-white mb-2">No projects found</h3>
          <p className="text-gray-400">Try adjusting your filters or create a new project.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.items.map(p => (
            <ProjectCard key={p.id} project={p} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}
"""

files["src/pages/ProjectForm.tsx"] = """import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { projectApi } from "../lib/projectApi";
import { ProjectStatus, ProjectPriority } from "../types/project";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

export default function ProjectForm() {
  const { projectId } = useParams();
  const isEditing = !!projectId;
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<ProjectStatus>(ProjectStatus.PLANNING);
  const [priority, setPriority] = useState<ProjectPriority>(ProjectPriority.MEDIUM);
  const [techStack, setTechStack] = useState("");
  const [loading, setLoading] = useState(isEditing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isEditing) {
      loadProject();
    }
  }, [projectId]);

  const loadProject = async () => {
    try {
      const data = await projectApi.get(projectId!);
      setName(data.name);
      setDescription(data.description || "");
      setStatus(data.status);
      setPriority(data.priority);
      setTechStack(data.tech_stack.join(", "));
    } catch (err) {
      setError("Failed to load project");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    
    const stack = techStack.split(",").map(s => s.trim()).filter(s => s.length > 0);
    
    try {
      if (isEditing) {
        await projectApi.update(projectId!, { name, description, status, priority, tech_stack: stack });
        navigate(`/projects/${projectId}`);
      } else {
        const p = await projectApi.create({ name, description, status, priority, tech_stack: stack });
        navigate(`/projects/${p.id}`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || "Failed to save project.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-gray-400">Loading...</div>;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">{isEditing ? "Edit Project" : "Create Project"}</h1>
      </div>

      <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-6">
        {error && <div className="p-3 text-sm text-red-500 bg-red-950/50 border border-red-900 rounded-md">{error}</div>}

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">Project Name *</label>
          <Input id="name" required value={name} onChange={e => setName(e.target.value)} />
        </div>

        <div>
          <label htmlFor="desc" className="block text-sm font-medium text-gray-300 mb-1">Description</label>
          <textarea 
            id="desc"
            className="flex min-h-[100px] w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            value={description}
            onChange={e => setDescription(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
            <select 
              className="h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100"
              value={status}
              onChange={e => setStatus(e.target.value as ProjectStatus)}
            >
              {Object.values(ProjectStatus).map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Priority</label>
            <select 
              className="h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100"
              value={priority}
              onChange={e => setPriority(e.target.value as ProjectPriority)}
            >
              {Object.values(ProjectPriority).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="tech" className="block text-sm font-medium text-gray-300 mb-1">Tech Stack (comma separated)</label>
          <Input id="tech" placeholder="e.g. React, TypeScript, FastAPI" value={techStack} onChange={e => setTechStack(e.target.value)} />
        </div>

        <div className="flex justify-end space-x-4 pt-4 border-t border-gray-800">
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>Cancel</Button>
          <Button type="submit" isLoading={saving}>
            {isEditing ? "Save Changes" : "Create Project"}
          </Button>
        </div>
      </form>
    </div>
  );
}
"""

files["src/pages/ProjectDetails.tsx"] = """import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { projectApi } from "../lib/projectApi";
import { Project } from "../types/project";
import { Button } from "../components/ui/Button";

export default function ProjectDetails() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    try {
      const data = await projectApi.get(projectId!);
      setProject(data);
    } catch (err) {
      setError("Project not found");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this project?")) {
      try {
        await projectApi.delete(projectId!);
        navigate("/projects");
      } catch (err) {
        alert("Failed to delete project");
      }
    }
  };

  if (loading) return <div className="text-gray-400">Loading...</div>;
  if (error || !project) return <div className="text-red-400">{error}</div>;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <Link to="/projects" className="text-sm text-blue-500 hover:text-blue-400 mb-2 inline-block">&larr; Back to projects</Link>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            {project.name}
            <span className="text-xs px-2 py-1 rounded-full border bg-gray-800 text-gray-300 border-gray-700 font-normal">
              {project.status}
            </span>
          </h1>
          <p className="mt-2 text-gray-400 max-w-2xl">{project.description || "No description provided."}</p>
        </div>
        <div className="flex space-x-3">
          <Link to={`/projects/${project.id}/edit`}>
            <Button variant="outline">Edit</Button>
          </Link>
          <Button variant="outline" className="text-red-400 border-red-900/50 hover:bg-red-950/30" onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-medium text-white mb-4">Project Overview</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="block text-sm text-gray-500">Priority</span>
                <span className="text-gray-200">{project.priority}</span>
              </div>
              <div>
                <span className="block text-sm text-gray-500">Tech Stack</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {project.tech_stack.length > 0 ? project.tech_stack.map(tech => (
                    <span key={tech} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded-md border border-gray-700">{tech}</span>
                  )) : <span className="text-gray-500 text-sm">None</span>}
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 border-dashed opacity-75">
            <h3 className="text-lg font-medium text-white mb-2">Tasks & Kanban</h3>
            <p className="text-gray-400 text-sm mb-4">Task management is coming in Phase 3.</p>
            <Button disabled variant="secondary">Add Task</Button>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 border-dashed opacity-75">
            <h3 className="text-lg font-medium text-white mb-2">AI Analysis</h3>
            <p className="text-gray-400 text-sm mb-4">AI Assistant and repository integrations are coming in future phases.</p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider mb-4">Details</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Created</span>
                <span className="text-gray-300">{new Date(project.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Last Updated</span>
                <span className="text-gray-300">{new Date(project.updated_at || project.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
"""

for path, content in files.items():
    with open(os.path.join(base_dir, path), "w", encoding="utf-8") as f:
        f.write(content)

print("Frontend phase 2 part 2 generated.")
