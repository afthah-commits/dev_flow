import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { projectApi } from "../lib/projectApi";
import { analyticsApi } from "../lib/analyticsApi";
import { Project } from "../types/project";
import { DashboardOverview } from "../types/analytics";
import { ProjectCard } from "../components/ProjectCard";
import { api } from "../lib/axios";

export default function Dashboard() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeSprints, setActiveSprints] = useState<any[]>([]);
  const [stats, setStats] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [res, statsRes, sprintsRes] = await Promise.all([
        projectApi.list({ page_size: 4, sort_by: "updated_at", sort_order: "desc" }),
        analyticsApi.getDashboard(),
        api.get("/dashboard/sprints/active").then((r: any) => r.data)
      ]);
      setProjects(res.items);
      setStats(statsRes);
      setActiveSprints(sprintsRes);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await projectApi.delete(id);
      loadData();
    } catch (error) {
      console.error(error);
      alert("Failed to delete project");
    }
  };

  

  if (loading) {
    return <div className="text-gray-400">Loading dashboard...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Welcome back, {user?.name}</h1>
          <p className="mt-1 text-gray-400">Here's what's happening across your workspace.</p>
        </div>
        <Link 
          to="/projects/new" 
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
        >
          Create Project
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 flex flex-col">
          <span className="text-sm font-medium text-gray-400">Active Projects</span>
          <span className="text-3xl font-bold mt-2 text-emerald-400">{stats?.active_projects || 0}</span>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 flex flex-col">
          <span className="text-sm font-medium text-gray-400">Total Tasks</span>
          <span className="text-3xl font-bold mt-2 text-blue-400">{stats?.total_tasks || 0}</span>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 flex flex-col">
          <span className="text-sm font-medium text-gray-400">Completed Tasks</span>
          <span className="text-3xl font-bold mt-2 text-purple-400">{stats?.completed_tasks || 0}</span>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 flex flex-col">
          <span className="text-sm font-medium text-gray-400">Overdue Tasks</span>
          <span className="text-3xl font-bold mt-2 text-red-400">{stats?.overdue_tasks || 0}</span>
        </div>
      </div>
      
      {activeSprints.length > 0 && (
        <div>
          <h2 className="text-xl font-bold text-white mb-4">Active Sprints</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {activeSprints.map(sprint => (
              <div key={sprint.id} className="bg-gray-900 border border-gray-800 rounded-lg p-5">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-sm text-gray-500 font-medium">{sprint.project_name}</span>
                  <span className="text-xs font-mono text-gray-500">{sprint.key}</span>
                </div>
                <h3 className="font-bold text-lg text-white mb-4">{sprint.sprint_name}</h3>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Progress</span>
                    <span className="text-white">{Math.round(sprint.progress)}%</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${Math.round(sprint.progress)}%` }}></div>
                  </div>
                </div>
                
                <div className="mt-4 flex justify-between text-sm border-t border-gray-800 pt-3 text-gray-400">
                  <span>{sprint.remaining_points !== undefined ? sprint.remaining_points : (sprint.total_points - sprint.completed_points)} pts left</span>
                  <span>Due: {sprint.end_date ? new Date(sprint.end_date).toLocaleDateString() : 'N/A'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">Recent Projects</h2>
          <Link to="/projects" className="text-sm text-blue-500 hover:text-blue-400 transition-colors">
            View all projects &rarr;
          </Link>
        </div>
        
        {projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((p: any) => (
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
