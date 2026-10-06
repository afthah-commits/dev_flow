import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { projectApi } from "../lib/projectApi";
import { analyticsApi } from "../lib/analyticsApi";
import { dashboardApi } from "../lib/dashboardApi";
import { DashboardWidgetPlacement } from "../types/dashboard";
import { Project } from "../types/project";
import { DashboardOverview } from "../types/analytics";
import { ProjectCard } from "../components/ProjectCard";
import { api } from "../lib/axios";

// Phase 45 — widget registry. IDs mirror the backend WIDGET_REGISTRY; the
// backend is the security boundary and filters widgets the user cannot see.
const WIDGET_TITLES: Record<string, string> = {
  stats: "Overview Stats",
  active_sprints: "Active Sprints",
  recent_projects: "Recent Projects",
};
const DEFAULT_WIDGETS: DashboardWidgetPlacement[] = [
  { id: "stats", visible: true },
  { id: "active_sprints", visible: true },
  { id: "recent_projects", visible: true },
];

export default function Dashboard() {
  const { user } = useAuth();
  const [widgets, setWidgets] = useState<DashboardWidgetPlacement[]>(DEFAULT_WIDGETS);
  const [draft, setDraft] = useState<DashboardWidgetPlacement[]>([]);
  const [customizing, setCustomizing] = useState(false);
  const [savingLayout, setSavingLayout] = useState(false);
  const [layoutError, setLayoutError] = useState("");

  const [projects, setProjects] = useState<Project[]>([]);
  const [activeSprints, setActiveSprints] = useState<any[]>([]);
  const [stats, setStats] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Personal layout; falls back to defaults when unset or unreachable.
      let layoutWidgets = DEFAULT_WIDGETS;
      try {
        const layout = await dashboardApi.getLayout();
        if (layout?.widgets?.length) layoutWidgets = layout.widgets;
      } catch {
        /* defaults are fine */
      }
      setWidgets(layoutWidgets);

      const visible = new Set(layoutWidgets.filter(w => w.visible).map(w => w.id));
      const [statsRes, sprintsRes, projectsRes] = await Promise.all([
        visible.has("stats") ? analyticsApi.getDashboard().catch(() => null) : Promise.resolve(null),
        visible.has("active_sprints")
          ? api.get("/dashboard/sprints/active").then((r: any) => r.data).catch(() => [])
          : Promise.resolve([]),
        visible.has("recent_projects")
          ? projectApi.list({ page_size: 4, sort_by: "updated_at", sort_order: "desc" }).catch(() => ({ items: [] }))
          : Promise.resolve({ items: [] }),
      ]);
      setStats(statsRes);
      setActiveSprints(sprintsRes || []);
      setProjects((projectsRes as any)?.items || []);
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

  // --- Phase 45 customization mode ---
  const startCustomize = () => {
    setDraft(widgets.map(w => ({ ...w })));
    setLayoutError("");
    setCustomizing(true);
  };

  const toggleWidget = (id: string) => {
    setDraft(prev => prev.map(w => (w.id === id ? { ...w, visible: !w.visible } : w)));
  };

  const moveWidget = (index: number, dir: -1 | 1) => {
    setDraft(prev => {
      const next = [...prev];
      const target = index + dir;
      if (target < 0 || target >= next.length) return prev;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const handleSaveLayout = async () => {
    setSavingLayout(true);
    setLayoutError("");
    try {
      const saved = await dashboardApi.saveLayout(draft);
      setWidgets(saved.widgets);
      setCustomizing(false);
      await loadData();
    } catch {
      setLayoutError("Failed to save dashboard layout");
    } finally {
      setSavingLayout(false);
    }
  };

  const handleCancelCustomize = () => {
    setCustomizing(false);
    setDraft([]);
    setLayoutError("");
  };

  const handleResetLayout = async () => {
    setSavingLayout(true);
    setLayoutError("");
    try {
      const reset = await dashboardApi.resetLayout();
      setWidgets(reset.widgets);
      setCustomizing(false);
      await loadData();
    } catch {
      setLayoutError("Failed to restore default layout");
    } finally {
      setSavingLayout(false);
    }
  };

  if (loading) {
    return <div className="text-gray-400">Loading dashboard...</div>;
  }

  const visibleWidgets = widgets.filter(w => w.visible && WIDGET_TITLES[w.id]);

  const renderWidget = (id: string) => {
    switch (id) {
      case "stats":
        return (
          <div key={id} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
        );
      case "active_sprints":
        return activeSprints.length > 0 ? (
          <div key={id}>
            <h2 className="text-xl font-bold text-white mb-4">Active Sprints</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {activeSprints.map((sprint: any) => (
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
        ) : null;
      case "recent_projects":
        return (
          <div key={id}>
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
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Welcome back, {user?.name}</h1>
          <p className="mt-1 text-gray-400">Here's what's happening across your workspace.</p>
        </div>
        <div className="flex items-center gap-3">
          {!customizing && (
            <button
              onClick={startCustomize}
              className="border border-gray-600 hover:bg-gray-800 text-gray-200 px-4 py-2 rounded-md font-medium transition-colors"
              data-testid="customize-button"
            >
              Customize
            </button>
          )}
          <Link
            to="/projects/new"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
          >
            Create Project
          </Link>
        </div>
      </div>

      {layoutError && (
        <div className="p-3 text-sm text-red-500 bg-red-950/50 border border-red-900 rounded-md" role="alert">
          {layoutError}
        </div>
      )}

      {/* Customization panel */}
      {customizing && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5" data-testid="customize-panel">
          <h2 className="text-lg font-bold text-white mb-3">Customize Dashboard</h2>
          <p className="text-sm text-gray-400 mb-4">Choose which widgets to show and in which order.</p>
          <ul className="space-y-2 mb-4">
            {draft.map((w, i) => (
              <li key={w.id} className="flex items-center justify-between bg-gray-950 border border-gray-800 rounded-md px-3 py-2">
                <label className="inline-flex items-center gap-2 text-sm text-gray-200">
                  <input
                    type="checkbox"
                    checked={w.visible}
                    onChange={() => toggleWidget(w.id)}
                    data-testid={`widget-toggle-${w.id}`}
                  />
                  {WIDGET_TITLES[w.id] || w.id}
                </label>
                <span className="flex gap-1">
                  <button
                    type="button"
                    onClick={() => moveWidget(i, -1)}
                    disabled={i === 0}
                    className="px-2 text-gray-400 hover:text-white disabled:opacity-30"
                    data-testid={`widget-up-${w.id}`}
                    aria-label="Move up"
                  >
                    &uarr;
                  </button>
                  <button
                    type="button"
                    onClick={() => moveWidget(i, 1)}
                    disabled={i === draft.length - 1}
                    className="px-2 text-gray-400 hover:text-white disabled:opacity-30"
                    data-testid={`widget-down-${w.id}`}
                    aria-label="Move down"
                  >
                    &darr;
                  </button>
                </span>
              </li>
            ))}
          </ul>
          <div className="flex justify-end gap-3">
            <button
              onClick={handleResetLayout}
              disabled={savingLayout}
              className="text-sm text-gray-400 hover:text-white px-3 py-2"
              data-testid="reset-layout"
            >
              Restore Defaults
            </button>
            <button
              onClick={handleCancelCustomize}
              className="border border-gray-600 text-gray-200 px-4 py-2 rounded-md hover:bg-gray-800"
              data-testid="cancel-customize"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveLayout}
              disabled={savingLayout}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50"
              data-testid="save-layout"
            >
              {savingLayout ? "Saving..." : "Save Layout"}
            </button>
          </div>
        </div>
      )}

      {visibleWidgets.map(w => (
        <div key={w.id} data-testid={`widget-${w.id}`}>
          {renderWidget(w.id)}
        </div>
      ))}
    </div>
  );
}
