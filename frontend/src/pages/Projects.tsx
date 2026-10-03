import React, { useState, useEffect } from "react";
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
          {Object.values(ProjectStatus).map((s: any) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select 
          className="h-10 rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100 w-full md:w-auto"
          value={priority}
          onChange={(e) => setPriority(e.target.value as any)}
        >
          <option value="">All Priorities</option>
          {Object.values(ProjectPriority).map((p: any) => <option key={p} value={p}>{p}</option>)}
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
          {data?.items.map((p: any) => (
            <ProjectCard key={p.id} project={p} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}
