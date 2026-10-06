import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { projectTemplateApi } from "../lib/projectTemplateApi";
import { ProjectTemplate } from "../types/template";
import { TaskPriority } from "../types/task";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

const emptyTask = { title: "", description: "", checklist_items: "", label_names: "", priority: TaskPriority.MEDIUM as TaskPriority };

export default function Templates() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showArchived, setShowArchived] = useState(false);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [tasks, setTasks] = useState([{ ...emptyTask }]);
  const [saving, setSaving] = useState(false);

  // Create-project-from-template modal state
  const [applyTemplate, setApplyTemplate] = useState<ProjectTemplate | null>(null);
  const [projectName, setProjectName] = useState("");
  const [projectDesc, setProjectDesc] = useState("");
  const [creatingProject, setCreatingProject] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await projectTemplateApi.list(showArchived);
      setTemplates(data);
    } catch {
      setError("Failed to load templates");
    } finally {
      setLoading(false);
    }
  }, [showArchived]);

  useEffect(() => { load(); }, [load]);

  const openEditor = (t?: ProjectTemplate) => {
    if (t) {
      setEditingId(t.id);
      setName(t.name);
      setDescription(t.description || "");
      setTasks(t.tasks.length
        ? t.tasks.map(task => ({
            title: task.title,
            description: task.description || "",
            checklist_items: (task.checklist_items || []).join(", "),
            label_names: (task.label_names || []).join(", "),
            priority: task.priority,
          }))
        : [{ ...emptyTask }]);
    } else {
      setEditingId(null);
      setName("");
      setDescription("");
      setTasks([{ ...emptyTask }]);
    }
    setEditorOpen(true);
  };

  const closeEditor = () => { setEditorOpen(false); setError(""); };

  const handleSaveTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const payload = {
        name,
        description,
        tasks: tasks
          .filter(t => t.title.trim())
          .map((t, i) => ({
            title: t.title.trim(),
            description: t.description || undefined,
            priority: t.priority,
            position: i,
            label_names: t.label_names.split(",").map(s => s.trim()).filter(Boolean),
            checklist_items: t.checklist_items.split(",").map(s => s.trim()).filter(Boolean),
          })),
      };
      if (editingId) {
        await projectTemplateApi.update(editingId, payload);
      } else {
        await projectTemplateApi.create(payload);
      }
      closeEditor();
      await load();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save template");
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async (t: ProjectTemplate) => {
    try {
      await projectTemplateApi.archive(t.id);
      await load();
    } catch {
      setError("Failed to archive template");
    }
  };

  const handleDelete = async (t: ProjectTemplate) => {
    if (!window.confirm(`Delete template "${t.name}"? Projects already created from it are not affected.`)) return;
    try {
      await projectTemplateApi.delete(t.id);
      await load();
    } catch {
      setError("Failed to delete template");
    }
  };

  const openCreateProject = (t: ProjectTemplate) => {
    setApplyTemplate(t);
    setProjectName("");
    setProjectDesc("");
    setError("");
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applyTemplate) return;
    setCreatingProject(true);
    setError("");
    try {
      const res = await projectTemplateApi.createProject(applyTemplate.id, {
        name: projectName,
        description: projectDesc || undefined,
      });
      setApplyTemplate(null);
      navigate(`/projects/${res.project_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create project from template");
    } finally {
      setCreatingProject(false);
    }
  };

  const updateTask = (idx: number, patch: Partial<typeof emptyTask>) => {
    setTasks(prev => prev.map((t, i) => (i === idx ? { ...t, ...patch } : t)));
  };

  return (
    <div className="max-w-5xl mx-auto" data-testid="templates-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Project Templates</h1>
          <p className="text-gray-400 text-sm mt-1">Reusable blueprints for quickly creating standardized projects.</p>
        </div>
        <Button onClick={() => openEditor()}>New Template</Button>
      </div>

      {error && <div className="mb-4 p-3 text-sm text-red-500 bg-red-950/50 border border-red-900 rounded-md" role="alert">{error}</div>}

      <label className="inline-flex items-center gap-2 text-sm text-gray-400 mb-4">
        <input type="checkbox" checked={showArchived} onChange={e => setShowArchived(e.target.checked)} data-testid="show-archived" />
        Show archived
      </label>

      {loading ? (
        <div className="text-gray-400" data-testid="templates-loading">Loading...</div>
      ) : templates.length === 0 ? (
        <div className="text-center py-16 border border-gray-800 rounded-lg bg-gray-900" data-testid="templates-empty">
          <p className="text-gray-400">No templates yet. Create your first template to standardize project setup.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {templates.map(t => (
            <div key={t.id} className="bg-gray-900 border border-gray-800 rounded-lg p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    {t.name}
                    {t.is_archived && <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400">Archived</span>}
                  </h2>
                  {t.description && <p className="text-gray-400 text-sm mt-1">{t.description}</p>}
                  <p className="text-gray-500 text-xs mt-2" data-testid={`template-task-count-${t.id}`}>
                    {t.tasks.length} template task{t.tasks.length === 1 ? "" : "s"}
                  </p>
                  {t.tasks.length > 0 && (
                    <ul className="mt-3 space-y-1" data-testid={`template-preview-${t.id}`}>
                      {t.tasks.map(task => (
                        <li key={task.id} className="text-sm text-gray-300">
                          <span className="text-gray-500 mr-2">#{task.position + 1}</span>
                          {task.title}
                          {task.checklist_items?.length > 0 && (
                            <span className="text-gray-600 ml-2">({task.checklist_items.length} checklist items)</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="flex flex-col items-end gap-2 shrink-0">
                  <Button onClick={() => openCreateProject(t)} disabled={t.is_archived}>Create Project</Button>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => openEditor(t)}>Edit</Button>
                    {!t.is_archived && <Button variant="outline" onClick={() => handleArchive(t)}>Archive</Button>}
                    <Button variant="outline" onClick={() => handleDelete(t)}>Delete</Button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Template editor modal */}
      {editorOpen && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 overflow-y-auto">
          <form onSubmit={handleSaveTemplate} className="bg-gray-900 rounded-lg max-w-2xl w-full p-6 border border-gray-700" data-testid="template-editor">
            <h3 className="text-lg font-medium text-white mb-4">{editingId ? "Edit Template" : "New Template"}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Template Name *</label>
                <Input required value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Standard Web App Kickoff" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                <Input value={description} onChange={e => setDescription(e.target.value)} placeholder="What is this template for?" />
              </div>

              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-300">Template Tasks</label>
                {tasks.map((t, i) => (
                  <div key={i} className="border border-gray-800 rounded-md p-3 space-y-2 bg-gray-950">
                    <Input
                      placeholder={`Task ${i + 1} title`}
                      value={t.title}
                      onChange={e => updateTask(i, { title: e.target.value })}
                    />
                    <Input
                      placeholder="Description (optional)"
                      value={t.description}
                      onChange={e => updateTask(i, { description: e.target.value })}
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <Input
                        placeholder="Checklist items (comma separated)"
                        value={t.checklist_items}
                        onChange={e => updateTask(i, { checklist_items: e.target.value })}
                      />
                      <Input
                        placeholder="Label names (comma separated)"
                        value={t.label_names}
                        onChange={e => updateTask(i, { label_names: e.target.value })}
                      />
                    </div>
                    <select
                      className="h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100"
                      value={t.priority}
                      onChange={e => updateTask(i, { priority: e.target.value as TaskPriority })}
                    >
                      {Object.values(TaskPriority).map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                    {tasks.length > 1 && (
                      <button type="button" className="text-xs text-red-400 hover:text-red-300" onClick={() => setTasks(prev => prev.filter((_, j) => j !== i))}>
                        Remove task
                      </button>
                    )}
                  </div>
                ))}
                <Button type="button" variant="outline" onClick={() => setTasks(prev => [...prev, { ...emptyTask }])}>
                  Add Task
                </Button>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-800">
              <Button type="button" variant="outline" onClick={closeEditor}>Cancel</Button>
              <Button type="submit" isLoading={saving}>{editingId ? "Save Changes" : "Create Template"}</Button>
            </div>
          </form>
        </div>
      )}

      {/* Create project from template modal */}
      {applyTemplate && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleCreateProject} className="bg-gray-900 rounded-lg max-w-md w-full p-6 border border-gray-700" data-testid="create-project-modal">
            <h3 className="text-lg font-medium text-white mb-1">Create Project from Template</h3>
            <p className="text-sm text-gray-400 mb-4" data-testid="apply-template-name">
              Using template: <span className="text-gray-200 font-medium">{applyTemplate.name}</span>
              <span className="text-gray-500"> ({applyTemplate.tasks.length} tasks will be created)</span>
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Project Name *</label>
                <Input required value={projectName} onChange={e => setProjectName(e.target.value)} placeholder="e.g. Customer Portal v2" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                <Input value={projectDesc} onChange={e => setProjectDesc(e.target.value)} placeholder="Optional description" />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-800">
              <Button type="button" variant="outline" onClick={() => setApplyTemplate(null)}>Cancel</Button>
              <Button type="submit" isLoading={creatingProject} data-testid="apply-template-submit">Create Project</Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
