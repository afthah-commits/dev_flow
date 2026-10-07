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

const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

// Phase 49 client-side editor bounds (mirrored server-side on Apply).
const MAX_DEPTH = 3;          // levels 0..2
const MAX_CHILDREN = 8;
const MAX_NODES = 32;
const MAX_TITLE = 200;
const MAX_DESC = 1000;

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

function deepCloneTree(nodes: AIPlanningSuggestion[]): AIPlanningSuggestion[] {
  return nodes.map(n => ({ ...n, children: n.children ? deepCloneTree(n.children) : undefined }));
}

function countNodes(nodes: AIPlanningSuggestion[]): number {
  return nodes.reduce((s, n) => s + 1 + countNodes(n.children || []), 0);
}

interface EditDraft {
  title: string;
  description: string;
  priority: string;
  estimated_points: string; // kept as string while typing; parsed on save
}

export function ProjectAIPlanning({ project, tasks: tasksProp, onChanged }: Props) {
  const [fetchedTasks, setFetchedTasks] = useState<{ id: string; title: string }[]>([]);
  const [taskId, setTaskId] = useState<string>('');
  const [analysis, setAnalysis] = useState<AIPlanningAnalysis | null>(null);
  // Phase 49 — editable draft tree (preview state; never persisted until Apply)
  const [draft, setDraft] = useState<AIPlanningSuggestion[] | null>(null);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<EditDraft | null>(null);
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
    setDraft(null);
    setEditingKey(null);
    setSelected(new Set());
    setExpanded(new Set());
    try {
      const res = await aiApi.analyzePlanning(project.id, taskId || undefined);
      setAnalysis(res);
      setDraft(deepCloneTree(res.suggested_breakdown));
      // Default: all suggestions pre-selected and expanded (user can
      // unselect/edit and must still press Apply).
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

  if (!analysis || !draft) {
    return (
      <AnalyzeSection
        project={project}
        tasks={tasks}
        taskId={taskId}
        setTaskId={setTaskId}
        loading={loading}
        error={error}
        appliedMsg={appliedMsg}
        handleAnalyze={handleAnalyze}
      />
    );
  }

  const flat = flatten(draft);
  const visibleFlat = flat.filter(f => {
    const parts = f.key.split('.');
    for (let i = 1; i < parts.length; i++) {
      if (!expanded.has(parts.slice(0, i).join('.'))) return false;
    }
    return true;
  });
  const selectedNodes = flat.filter(f => selected.has(f.key));
  const totalEffort = selectedNodes.reduce((sum, f) => sum + (f.node.estimated_points ?? 0), 0);
  const maxDepth = flat.reduce((m, f) => Math.max(m, f.depth), 0);
  const depthReachedMax = maxDepth >= MAX_DEPTH - 1; // 3 levels = depth 0..2
  const nodeCount = countNodes(draft);

  // ---- client-side validation warnings (server remains authoritative) ----
  const warnings: string[] = [];
  flat.forEach(f => {
    if (!f.node.title.trim()) warnings.push(`Node at ${f.key}: title is empty`);
    if (f.node.title.length > MAX_TITLE) warnings.push(`Node at ${f.key}: title too long`);
    if ((f.node.children || []).length > MAX_CHILDREN) warnings.push(`Node at ${f.key}: more than ${MAX_CHILDREN} children`);
    if (f.node.estimated_points != null && (f.node.estimated_points < 0 || f.node.estimated_points > 100)) {
      warnings.push(`Node at ${f.key}: estimated points out of range (0-100)`);
    }
  });
  if (maxDepth >= MAX_DEPTH) warnings.push('Tree exceeds maximum depth (3 levels)');
  if (nodeCount > MAX_NODES) warnings.push(`Tree exceeds maximum node count (${MAX_NODES})`);
  const ids = flat.map(f => f.node.suggestion_id).filter(Boolean);
  if (new Set(ids).size !== ids.length) warnings.push('Duplicate suggestion ids detected');

  const updateNode = (key: string, updater: (n: AIPlanningSuggestion) => AIPlanningSuggestion) => {
    setDraft(prev => {
      if (!prev) return prev;
      const clone = deepCloneTree(prev);
      const parts = key.split('.').map(Number);
      const walk = (items: AIPlanningSuggestion[], depth: number): AIPlanningSuggestion[] | null => {
        const idx = parts[depth];
        if (depth === parts.length - 1) {
          items[idx] = updater(items[idx]);
          return items;
        }
        const child = items[idx].children;
        if (!child) return null;
        return walk(child, depth + 1) ? items : null;
      };
      walk(clone, 0);
      return clone;
    });
  };

  const startEdit = (key: string) => {
    const f = flat.find(x => x.key === key);
    if (!f) return;
    setEditingKey(key);
    setEditDraft({
      title: f.node.title,
      description: f.node.description || '',
      priority: f.node.priority,
      estimated_points: f.node.estimated_points != null ? String(f.node.estimated_points) : '',
    });
  };

  const saveEdit = () => {
    if (!editingKey || !editDraft) return;
    const ptsRaw = editDraft.estimated_points.trim();
    let points: number | undefined = undefined;
    if (ptsRaw !== '') {
      const parsed = Number(ptsRaw);
      if (!Number.isFinite(parsed) || parsed < 0 || parsed > 100) {
        setError('Estimated points must be a number between 0 and 100.');
        return;
      }
      points = parsed;
    }
    updateNode(editingKey, n => ({
      ...n,
      title: editDraft.title.trim().slice(0, MAX_TITLE),
      description: editDraft.description.trim().slice(0, MAX_DESC),
      priority: PRIORITIES.includes(editDraft.priority) ? editDraft.priority : 'MEDIUM',
      estimated_points: points,
    }));
    setEditingKey(null);
    setEditDraft(null);
    setError(null);
  };

  const cancelEdit = () => {
    setEditingKey(null);
    setEditDraft(null);
  };

  const addChild = (key: string) => {
    const f = flat.find(x => x.key === key);
    if (!f) return;
    if (f.depth + 1 > MAX_DEPTH - 1) {
      setError(`Cannot add child: maximum depth (${MAX_DEPTH} levels) reached.`);
      return;
    }
    if ((f.node.children || []).length >= MAX_CHILDREN) {
      setError(`Cannot add child: maximum ${MAX_CHILDREN} children per node.`);
      return;
    }
    if (countNodes(draft) >= MAX_NODES) {
      setError(`Cannot add child: maximum ${MAX_NODES} nodes.`);
      return;
    }
    const child: AIPlanningSuggestion = {
      title: 'New sub-suggestion', description: '', priority: 'MEDIUM',
      suggestion_id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      estimated_points: undefined, level: f.depth + 1,
      parent_suggestion_id: f.node.suggestion_id || null, children: [],
    };
    const newClone = deepCloneTree(draft);
    {
      const parts = key.split('.').map(Number);
      const walk = (items: AIPlanningSuggestion[], depth: number): AIPlanningSuggestion => {
        const item = items[parts[depth]];
        if (depth === parts.length - 1) return item;
        return walk(item.children!, depth + 1);
      };
      const parent = walk(newClone, 0);
      parent.children = [...(parent.children || []), child];
    }
    setDraft(newClone);
    setExpanded(prev => new Set(prev).add(key));
    // select the newly added child (last child of `key`)
    setSelected(prev => {
      const next = new Set(prev);
      next.add(`${key}.${(f.node.children || []).length}`);
      return next;
    });
  };

  const deleteNode = (key: string) => {
    const f = flat.find(x => x.key === key);
    if (!f) return;
    const hasChildren = (f.node.children || []).length > 0;
    if (hasChildren && !window.confirm(`Delete "${f.node.title}" and its ${f.node.children!.length} sub-suggestion(s)?`)) {
      return;
    }
    setDraft(prev => {
      if (!prev) return prev;
      const clone = deepCloneTree(prev);
      const parts = key.split('.').map(Number);
      const parentPath = parts.slice(0, -1);
      const idx = parts[parts.length - 1];
      const walk = (items: AIPlanningSuggestion[], depth: number): AIPlanningSuggestion[] => {
        if (depth === parentPath.length) {
          items.splice(idx, 1);
          return items;
        }
        return walk(items[parts[depth]].children!, depth + 1);
      };
      if (parentPath.length === 0) clone.splice(idx, 1);
      else walk(clone, 0);
      return clone;
    });
    // drop selection for the node and its descendants (keys shift; keep it
    // simple by removing key-prefixed selections)
    setSelected(prev => {
      const next = new Set(prev);
      [...next].forEach(k => { if (k === key || k.startsWith(key + '.')) next.delete(k); });
      return next;
    });
    if (editingKey === key) { setEditingKey(null); setEditDraft(null); }
  };

  // Valid move targets: any node that is not the mover itself and not one of
  // its descendants (prevents cycles), with room below depth 3.
  const moveTargets = (key: string): FlatNode[] => {
    return flat.filter(f =>
      f.key !== key &&
      !key.startsWith(f.key + '.') && // descendant of mover? mover key startswith f.key
      !f.key.startsWith(key + '.') && // mover is descendant of f (would create cycle)
      f.depth + 1 <= MAX_DEPTH - 1 &&
      (f.node.children || []).length < MAX_CHILDREN
    );
  };

  const moveNode = (key: string, targetKey: string) => {
    const mover = flat.find(x => x.key === key);
    const target = flat.find(x => x.key === targetKey);
    if (!mover || !target) return;
    if (target.depth + 1 > MAX_DEPTH - 1) {
      setError(`Cannot move: would exceed maximum depth (${MAX_DEPTH} levels).`);
      return;
    }
    // Selection is preserved by node identity across the move. The clone
    // below is structural (new arrays, same node objects) so identity holds.
    const selectedNodesByIdentity = new Set<AIPlanningSuggestion>();
    flat.forEach(f => { if (selected.has(f.key)) selectedNodesByIdentity.add(f.node); });

    // Structural copy: fresh arrays at every level, SAME node objects —
    // so node identity (and thus selection) survives the move.
    const structuralCopy = (items: AIPlanningSuggestion[]): AIPlanningSuggestion[] =>
      items.map(n => { n.children = n.children ? structuralCopy(n.children) : n.children; return n; });
    const clone = structuralCopy(draft);
    const detached = mover.node;
    const parts = key.split('.').map(Number);
    const parentPath = parts.slice(0, -1);
    const idx = parts[parts.length - 1];
    if (parentPath.length === 0) clone.splice(idx, 1);
    else {
      const walk = (items: AIPlanningSuggestion[], depth: number) => {
        if (depth === parentPath.length) { items.splice(idx, 1); return; }
        walk(items[parts[depth]].children!, depth + 1);
      };
      walk(clone, 0);
    }
    const tParts = targetKey.split('.').map(Number);
    const walkT = (items: AIPlanningSuggestion[], depth: number): AIPlanningSuggestion => {
      const item = items[tParts[depth]];
      if (depth === tParts.length - 1) return item;
      return walkT(item.children!, depth + 1);
    };
    const t = walkT(clone, 0);
    detached.level = target.depth + 1;
    detached.parent_suggestion_id = t.suggestion_id || null;
    t.children = [...(t.children || []), detached];

    setDraft(clone);
    const nextSel = new Set<string>();
    flatten(clone).forEach(f => { if (selectedNodesByIdentity.has(f.node)) nextSel.add(f.key); });
    setSelected(nextSel);
    setExpanded(prev => new Set(prev).add(targetKey));
    setError(null);
  };

  const toggle = (key: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
        flat.filter(f => f.key.startsWith(key + '.')).forEach(f => next.delete(f.key));
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
      const suggestions = toPayload(draft, null);
      const res = await aiApi.applyPlanningSuggestions(project.id, analysis.task_id, suggestions);
      setAppliedMsg(`Applied ${res.applied} subtask${res.applied === 1 ? '' : 's'}.`);
      setAnalysis(null);
      setDraft(null);
      setSelected(new Set());
      setExpanded(new Set());
      onChanged?.();
    } catch (e: any) {
      const detail = e.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to apply suggestions.');
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
      appliedMsg={appliedMsg}
      handleAnalyze={handleAnalyze}
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

        {/* Progressive breakdown editor (preview only) */}
        {draft.length > 0 && (
          <div className="bg-gray-950 border border-gray-800 rounded p-3" data-testid="planning-breakdown">
            <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
              <div className="text-[10px] uppercase tracking-wider text-gray-500">Suggested Task Breakdown (preview — editable)</div>
              <div className="text-xs text-gray-300 flex gap-3">
                <span data-testid="planning-total-effort">Selected effort: <span className="font-bold text-white">{totalEffort}</span> pts</span>
                <span data-testid="planning-node-count">{selectedNodes.length}/{nodeCount} nodes</span>
                <span data-testid="planning-tree-depth">depth {maxDepth + 1}/{MAX_DEPTH}</span>
              </div>
            </div>
            {depthReachedMax && (
              <div className="text-[10px] text-yellow-400 mb-2" data-testid="max-depth-warning">
                Maximum suggested depth reached (3 levels).
              </div>
            )}
            {warnings.length > 0 && (
              <div className="bg-yellow-900/40 border border-yellow-800 text-yellow-200 text-xs rounded p-2 mb-2" data-testid="editor-warnings">
                {warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
              </div>
            )}
            <ul className="space-y-1">
              {visibleFlat.map(({ key, node, depth }) => {
                const isExpanded = expanded.has(key);
                const isEditing = editingKey === key;
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
                      {isEditing && editDraft ? (
                        <div className="flex-1 space-y-1" data-testid={`suggestion-edit-${key}`}>
                          <input
                            value={editDraft.title}
                            onChange={e => setEditDraft({ ...editDraft, title: e.target.value })}
                            data-testid={`edit-title-${key}`}
                            className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-white"
                            placeholder="Title"
                          />
                          <input
                            value={editDraft.description}
                            onChange={e => setEditDraft({ ...editDraft, description: e.target.value })}
                            data-testid={`edit-description-${key}`}
                            className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-white"
                            placeholder="Description"
                          />
                          <div className="flex gap-2">
                            <select
                              value={editDraft.priority}
                              onChange={e => setEditDraft({ ...editDraft, priority: e.target.value })}
                              data-testid={`edit-priority-${key}`}
                              className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-white"
                            >
                              {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                            </select>
                            <input
                              value={editDraft.estimated_points}
                              onChange={e => setEditDraft({ ...editDraft, estimated_points: e.target.value })}
                              data-testid={`edit-points-${key}`}
                              className="w-20 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-white"
                              placeholder="pts"
                            />
                            <button onClick={saveEdit} data-testid={`edit-save-${key}`}
                              className="px-2 py-1 bg-green-700 hover:bg-green-600 text-white rounded text-xs">Save</button>
                            <button onClick={cancelEdit} data-testid={`edit-cancel-${key}`}
                              className="px-2 py-1 text-gray-400 hover:text-white text-xs">Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="flex-1">
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
                          <div className="flex items-center gap-1">
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
                            <button onClick={() => startEdit(key)} data-testid={`suggestion-edit-${key}`}
                              title="Edit" className="text-gray-500 hover:text-blue-300 text-xs px-1">✎</button>
                            <button onClick={() => addChild(key)} data-testid={`suggestion-add-child-${key}`}
                              title="Add child" className="text-gray-500 hover:text-green-300 text-xs px-1">＋</button>
                            <button onClick={() => deleteNode(key)} data-testid={`suggestion-delete-${key}`}
                              title="Delete" className="text-gray-500 hover:text-red-300 text-xs px-1">✕</button>
                            {moveTargets(key).length > 0 && (
                              <select
                                value=""
                                onChange={e => e.target.value && moveNode(key, e.target.value)}
                                data-testid={`suggestion-move-${key}`}
                                title="Move under…"
                                className="bg-gray-900 border border-gray-700 rounded text-[10px] text-gray-400 px-1"
                              >
                                <option value="">Move under…</option>
                                {moveTargets(key).map(t => (
                                  <option key={t.key} value={t.key}>{'· '.repeat(t.depth)}{t.node.title.slice(0, 30)}</option>
                                ))}
                              </select>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                    {node.children && node.children.length > 0 && !isExpanded && !isEditing && (
                      <div className="ml-10 text-[10px] text-gray-600" data-testid={`suggestion-collapsed-${key}`}>
                        {node.children.length} sub-suggestion{node.children.length === 1 ? '' : 's'} hidden
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
            <div className="text-[10px] text-gray-600 mt-2">
              Edits stay in preview until Apply. Nothing is created until you press Apply. Deselecting a parent deselects its children. The server re-validates every edit.
            </div>
            <div className="flex justify-end gap-2 mt-3">
              <button
                onClick={() => { setAnalysis(null); setDraft(null); setSelected(new Set()); setExpanded(new Set()); }}
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
  project, tasks, taskId, setTaskId, loading, error, handleAnalyze, children, appliedMsg,
}: {
  project: { id: string; name: string };
  tasks: { id: string; title: string }[];
  taskId: string;
  setTaskId: (v: string) => void;
  loading: boolean;
  error: string | null;
  handleAnalyze: () => void;
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
