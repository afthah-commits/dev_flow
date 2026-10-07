import React, { useEffect, useState } from 'react';
import { aiApi } from '../lib/aiApi';
import { taskApi } from '../lib/taskApi';
import { AIPlanningAnalysis, AIPlanningSuggestion } from '../types/ai';

interface Props {
  project: { id: string; name: string };
  tasks?: { id: string; title: string }[];
  onChanged?: () => void;
}

const COMPLEXITY_COLOR: Record<string, string> = {
  LOW: 'text-green-400 border-green-800 bg-green-900/30',
  MEDIUM: 'text-yellow-400 border-yellow-800 bg-yellow-900/30',
  HIGH: 'text-red-400 border-red-800 bg-red-900/30',
};

const CONFIDENCE_COLOR: Record<string, string> = {
  HIGH: 'text-green-400',
  MEDIUM: 'text-yellow-400',
  LOW: 'text-gray-400',
};

// Flattened view model: a suggestion plus its path within the draft tree,
// keyed by the index path (e.g. "0.2.1") for stable React keys and
// deselect-cascades-to-children semantics.
interface FlatNode {
  key: string;
  node: AIPlanningSuggestion;
  depth: number;
  parentKey: string | null;
}

function flatten(nodes: AIPlanningSuggestion[]): FlatNode[] {
  const out: FlatNode[] = [];
  const walk = (items: AIPlanningSuggestion[], depth: number, parentKey: string | null) => {
    items.forEach((node, i) => {
      const key = parentKey === null ? String(i) : `${parentKey}.${i}`;
      out.push({ key, node, depth, parentKey });
      if (node.children?.length) walk(node.children, depth + 1, key);
    });
  };
  walk(nodes, 0, null);
  return out;
}

export function ProjectAIPlanning({ project, tasks: tasksProp, onChanged }: Props) {
  const [fetchedTasks, setFetchedTasks] = useState<{ id: string; title: string }[]>([]);
  const [taskId, setTaskId] = useState<string>('');
  const [analysis, setAnalysis] = useState<AIPlanningAnalysis | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appliedMsg, setAppliedMsg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (tasksProp && tasksProp.length) {
      setFetchedTasks(tasksProp);
      return;
    }
    (async () => {
      try {
        const res: any = await taskApi.list(project.id, { page_size: 100 });
        const items: any[] = res?.items ?? res ?? [];
        if (!cancelled) setFetchedTasks(items.map((t: any) => ({ id: t.id, title: t.title })));
      } catch {
        if (!cancelled) setFetchedTasks([]);
      }
    })();
    return () => { cancelled = true; };
  }, [project.id]);

  const tasks = tasksProp && tasksProp.length ? tasksProp : fetchedTasks;

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setAppliedMsg(null);
    setAnalysis(null);
    setSelected(new Set());
    setExpanded(new Set());
    try {
      const res = await aiApi.analyzePlanning(project.id, taskId || undefined);
      setAnalysis(res);
      // Default: all suggestions pre-selected and expanded (user can
      // unselect/collapse and must still press Apply).
      const keys = new Set<string>();
      const expandedKeys = new Set<string>();
      flatten(res.suggested_breakdown).forEach(f => {
        keys.add(f.key);
        if (f.depth > 0) expandedKeys.add(f.parentKey!);
      });
      setSelected(keys);
      setExpanded(expandedKeys);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'AI planning failed.');
    } finally {
      setLoading(false);
    }
  };

  if (!analysis) {
    return (
      <AnalyzeSection
        project={project}
        tasks={tasks}
        taskId={taskId}
        setTaskId={setTaskId}
        loading={loading}
        error={error}
        handleAnalyze={handleAnalyze}
        expandedUI={false}
        appliedMsg={appliedMsg}
      />
    );
  }

  const flat = flatten(analysis.suggested_breakdown);
  const visibleFlat = flat.filter(f => {
    // A node is visible when every ancestor is expanded.
    const parts = f.key.split('.');
    for (let i = 1; i < parts.length; i++) {
      if (!expanded.has(parts.slice(0, i).join('.'))) return false;
    }
    return true;
  });
  const selectedNodes = flat.filter(f => selected.has(f.key));
  const totalEffort = selectedNodes.reduce((sum, f) => sum + (f.node.estimated_points ?? 0), 0);
  const maxDepth = flat.reduce((m, f) => Math.max(m, f.depth), 0);
  const depthReachedMax = maxDepth >= 2; // 3 levels = depth 0..2

  const toggle = (key: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
        // deselect cascades to descendants
        flat
          .filter(f => f.key.startsWith(key + '.'))
          .forEach(f => next.delete(f.key));
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const toggleExpand = (key: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const handleApply = async () => {
    if (!analysis?.task_id || selectedNodes.length === 0) return;
    setApplying(true);
    setError(null);
    try {
      // Build the selected subtree, preserving hierarchy.
      const toPayload = (nodes: AIPlanningSuggestion[], parentKey: string | null): AIPlanningSuggestion[] => {
        const out: AIPlanningSuggestion[] = [];
        nodes.forEach((node, i) => {
          const key = parentKey === null ? String(i) : `${parentKey}.${i}`;
          if (selected.has(key)) {
            out.push({ ...node, children: node.children ? toPayload(node.children, key) : undefined });
          }
        });
        return out;
      };
      const suggestions = toPayload(analysis.suggested_breakdown, null);
      const res = await aiApi.applyPlanningSuggestions(project.id, analysis.task_id, suggestions);
      setAppliedMsg(`Applied ${res.applied} subtask${res.applied === 1 ? '' : 's'}.`);
      setAnalysis(null);
      setSelected(new Set());
      setExpanded(new Set());
      onChanged?.();
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to apply suggestions.');
    } finally {
      setApplying(false);
    }
  };

  return (
    <AnalyzeSection
      project={project}
      tasks={tasks}
      taskId={taskId}
      setTaskId={setTaskId}
      loading={loading}
      error={error}
      handleAnalyze={handleAnalyze}
      expandedUI
      appliedMsg={appliedMsg}
    >
      <div className="space-y-4" data-testid="planning-summary">
        {/* Estimate & complexity */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="bg-gray-950 border border-gray-800 rounded p-3">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Estimated Effort (story points)</div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white" data-testid="planning-estimate">{analysis.estimate_points}</span>
              <span className={`text-xs font-semibold ${CONFIDENCE_COLOR[analysis.estimate_confidence] || ''}`} data-testid="planning-confidence">
                {analysis.estimate_confidence} confidence
              </span>
            </div>
            <ul className="mt-2 space-y-0.5">
              {analysis.estimate_factors.map((f, i) => (
                <li key={i} className="text-xs text-gray-400">• {f}</li>
              ))}
            </ul>
            <div className="text-[10px] text-gray-600 mt-1">AI-assisted estimate — not historical truth.</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded p-3">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Complexity</div>
            <span className={`inline-block text-sm font-bold px-3 py-1 border rounded ${COMPLEXITY_COLOR[analysis.complexity] || ''}`} data-testid="planning-complexity">
              {analysis.complexity}
            </span>
            <ul className="mt-2 space-y-0.5">
              {analysis.complexity_factors.map((f, i) => (
                <li key={i} className="text-xs text-gray-400">• {f}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Sprint capacity */}
        {analysis.capacity && (
          <div className="bg-gray-950 border border-gray-800 rounded p-3" data-testid="planning-capacity">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Sprint Capacity</div>
            {analysis.capacity.status === 'INSUFFICIENT_DATA' ? (
              <div className="text-sm text-gray-400">Insufficient data</div>
            ) : (
              <div className="text-sm text-gray-300">
                {analysis.capacity.sprint_name}: {analysis.capacity.committed_points} / {analysis.capacity.capacity_points} pts committed
                {' '}({analysis.capacity.remaining_points} remaining){' '}
                <span className={analysis.capacity.status === 'OVER_CAPACITY' ? 'text-red-400 font-semibold' : 'text-green-400'}>
                  {analysis.capacity.status === 'OVER_CAPACITY' ? '⚠ Over capacity' : 'OK'}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Risks & missing info */}
        {(analysis.risks.length > 0 || analysis.missing_information.length > 0 || analysis.dependency_concerns.length > 0) && (
          <div className="bg-gray-950 border border-gray-800 rounded p-3" data-testid="planning-risks">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Risks &amp; Gaps</div>
            <ul className="space-y-1">
              {analysis.risks.map((r, i) => (
                <li key={`r${i}`} className="text-xs text-red-300">⚠ {r}</li>
              ))}
              {analysis.dependency_concerns.map((c, i) => (
                <li key={`d${i}`} className="text-xs text-yellow-300">⛓ {c}</li>
              ))}
              {analysis.missing_information.map((m, i) => (
                <li key={`m${i}`} className="text-xs text-gray-400">? {m}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Progressive breakdown (preview only) */}
        {analysis.suggested_breakdown.length > 0 && (
          <div className="bg-gray-950 border border-gray-800 rounded p-3" data-testid="planning-breakdown">
            <div className="flex items-center justify-between mb-2">
              <div className="text-[10px] uppercase tracking-wider text-gray-500">Suggested Task Breakdown (preview only)</div>
              <div className="text-xs text-gray-300" data-testid="planning-total-effort">
                Selected effort: <span className="font-bold text-white">{totalEffort}</span> pts
              </div>
            </div>
            {depthReachedMax && (
              <div className="text-[10px] text-yellow-400 mb-2" data-testid="max-depth-warning">
                Maximum suggested depth reached (3 levels).
              </div>
            )}
            <ul className="space-y-1">
              {visibleFlat.map(({ key, node, depth }) => {
                const isExpanded = expanded.has(key);
                return (
                  <li key={key}>
                    <div
                      className={`flex items-start gap-2 ${depth > 0 ? 'border-l-2 border-gray-800 ml-3 pl-3' : ''}`}
                      data-testid={`suggestion-row-${key}`}
                      data-depth={depth}
                    >
                      <input
                        type="checkbox"
                        checked={selected.has(key)}
                        onChange={() => toggle(key)}
                        data-testid={`suggestion-checkbox-${key}`}
                        className="mt-1"
                      />
                      <div>
                        <div className={`text-white ${depth === 0 ? 'text-sm font-semibold' : 'text-xs'}`}>
                          {node.title}
                          {node.estimated_points != null && (
                            <span className="text-[10px] text-blue-300 ml-2">{node.estimated_points} pts</span>
                          )}
                          <span className="text-[10px] text-gray-500 ml-1">({node.priority})</span>
                        </div>
                        {node.description && depth === 0 && (
                          <div className="text-xs text-gray-400">{node.description}</div>
                        )}
                      </div>
                      {node.children && node.children.length > 0 && (
                        <button
                          onClick={() => toggleExpand(key)}
                          data-testid={`suggestion-expand-${key}`}
                          className="text-gray-500 hover:text-gray-300 text-xs px-1"
                          aria-expanded={isExpanded}
                        >
                          {isExpanded ? '▾' : '▸'} {node.children.length} sub
                        </button>
                      )}
                    </div>
                    {node.children && node.children.length > 0 && !isExpanded && (
                      <div className="ml-10 text-[10px] text-gray-600" data-testid={`suggestion-collapsed-${key}`}>
                        {node.children.length} sub-suggestion{node.children.length === 1 ? '' : 's'} hidden
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
            <div className="text-[10px] text-gray-600 mt-2">Nothing is created until you press Apply. Only selected suggestions. Deselecting a parent deselects its children.</div>
            <div className="flex justify-end gap-2 mt-3">
              <button
                onClick={() => { setAnalysis(null); setSelected(new Set()); setExpanded(new Set()); }}
                data-testid="planning-cancel"
                className="px-4 py-2 text-gray-400 hover:text-white text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleApply}
                disabled={applying || selectedNodes.length === 0 || !analysis.task_id}
                data-testid="planning-apply"
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white rounded text-sm font-medium transition-colors"
              >
                {applying ? 'Applying…' : `Apply Selected (${selectedNodes.length})`}
              </button>
            </div>
            {!analysis.task_id && (
              <div className="text-[10px] text-gray-500 mt-1">Select a specific task to apply a breakdown to it.</div>
            )}
          </div>
        )}
      </div>
    </AnalyzeSection>
  );
}

function AnalyzeSection({
  project, tasks, taskId, setTaskId, loading, error, handleAnalyze, expandedUI, children, appliedMsg,
}: {
  project: { id: string; name: string };
  tasks: { id: string; title: string }[];
  taskId: string;
  setTaskId: (v: string) => void;
  loading: boolean;
  error: string | null;
  handleAnalyze: () => void;
  expandedUI: boolean;
  children?: React.ReactNode;
  appliedMsg?: string | null;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4" data-testid="ai-planning-panel">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          🧠 AI Planning &amp; Estimation
          <span className="text-[10px] uppercase tracking-wider bg-blue-900/50 text-blue-300 border border-blue-800 rounded-full px-2 py-0.5">Advisory</span>
        </h3>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-3" data-testid="planning-task-selector">
        <select
          value={taskId}
          onChange={e => setTaskId(e.target.value)}
          className="bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">Whole project</option>
          {tasks.map(t => (
            <option key={t.id} value={t.id}>{t.title}</option>
          ))}
        </select>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          data-testid="analyze-button"
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded text-sm font-medium transition-colors"
        >
          {loading ? 'Analyzing…' : 'Analyze Planning'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/80 text-red-200 p-3 rounded text-sm border border-red-700 mb-3" data-testid="planning-error">
          {error}
        </div>
      )}

      {appliedMsg && (
        <div className="bg-green-900/60 text-green-200 p-3 rounded text-sm border border-green-800 mb-3" data-testid="planning-applied">
          {appliedMsg}
        </div>
      )}

      {loading && (
        <div className="text-gray-400 text-sm flex items-center gap-2 py-4" data-testid="planning-loading">
          <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></span>
          <span>Analyzing with AI…</span>
        </div>
      )}

      {!loading && children}
    </div>
  );
}
