import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { projectApi } from "../lib/projectApi";
import { projectTemplateApi } from "../lib/projectTemplateApi";
import { ProjectTemplate } from "../types/template";
import { ProjectStatus, ProjectPriority } from "../types/project";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

export default function ProjectForm() {
  const { projectId } = useParams();
  const isEditing = !!projectId;
  const navigate = useNavigate();

  // Phase 44: blank vs. template mode for new projects
  const [mode, setMode] = useState<"blank" | "template">("blank");
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null);

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
    } else {
      // Phase 44: load available templates for the create-from-template option
      projectTemplateApi.list()
        .then(setTemplates)
        .catch(() => { /* templates are optional; blank creation must keep working */ });
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
    
    const stack = techStack.split(",").map((s: any) => s.trim()).filter((s: any) => s.length > 0);
    
    try {
      if (isEditing) {
        await projectApi.update(projectId!, { name, description, status, priority, tech_stack: stack });
        navigate(`/projects/${projectId}`);
      } else if (mode === "template" && selectedTemplate) {
        const res = await projectTemplateApi.createProject(selectedTemplate.id, { name, description });
        navigate(`/projects/${res.project_id}`);
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

      {/* Phase 44: blank vs. template creation (new projects only) */}
      {!isEditing && (
        <div className="mb-6 bg-gray-900 border border-gray-800 rounded-lg p-4" data-testid="creation-mode">
          <div className="flex flex-wrap gap-2 mb-3">
            <Button
              type="button"
              variant={mode === "blank" ? "primary" : "outline"}
              onClick={() => setMode("blank")}
              data-testid="mode-blank"
            >
              Blank Project
            </Button>
            <Button
              type="button"
              variant={mode === "template" ? "primary" : "outline"}
              onClick={() => setMode("template")}
              data-testid="mode-template"
              disabled={templates.length === 0}
            >
              From Template
            </Button>
          </div>
          {mode === "template" && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Template</label>
              <select
                className="h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100"
                value={selectedTemplate?.id || ""}
                onChange={e => setSelectedTemplate(templates.find(t => t.id === e.target.value) || null)}
                data-testid="template-select"
              >
                <option value="">Select a template...</option>
                {templates.map(t => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.tasks.length} tasks)
                  </option>
                ))}
              </select>
              {selectedTemplate && (
                <p className="text-xs text-gray-500 mt-2" data-testid="template-hint">
                  {selectedTemplate.tasks.length} template task{selectedTemplate.tasks.length === 1 ? "" : "s"} will be copied into the new project.
                </p>
              )}
            </div>
          )}
        </div>
      )}

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
              {Object.values(ProjectStatus).map((s: any) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Priority</label>
            <select 
              className="h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100"
              value={priority}
              onChange={e => setPriority(e.target.value as ProjectPriority)}
            >
              {Object.values(ProjectPriority).map((p: any) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="tech" className="block text-sm font-medium text-gray-300 mb-1">Tech Stack (comma separated)</label>
          <Input id="tech" placeholder="e.g. React, TypeScript, FastAPI" value={techStack} onChange={e => setTechStack(e.target.value)} />
        </div>

        <div className="flex justify-end space-x-4 pt-4 border-t border-gray-800">
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>Cancel</Button>
          <Button type="submit" isLoading={saving} data-testid="project-submit">
            {isEditing ? "Save Changes" : "Create Project"}
          </Button>
        </div>
      </form>
    </div>
  );
}
