import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  workflowApi,
  StudioGraph,
  WorkflowState,
  WorkflowTransition,
  ValidationResult,
  SimulationResult,
  WorkflowVersion,
  WorkflowExecution,
  AIWorkflowSuggestion,
  FormFieldDef,
} from '../lib/workflowApi';
import { useRealtimeEvent } from '../hooks/useRealtime';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATE_TYPES = ['INITIAL', 'NORMAL', 'IN_PROGRESS', 'WAITING', 'APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED'];
const CONDITION_OPERATORS = ['EQUALS', 'NOT_EQUALS', 'CONTAINS', 'NOT_CONTAINS', 'GREATER_THAN', 'LESS_THAN', 'GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL', 'IS_EMPTY', 'IS_NOT_EMPTY'];
const ACTION_TYPES = ['CREATE_TASK', 'CREATE_COMMENT', 'UPDATE_TASK', 'SEND_NOTIFICATION', 'CREATE_AUDIT_EVENT', 'TRIGGER_AUTOMATION', 'REQUEST_APPROVAL'];
const NODE_W = 180;
const NODE_H = 76;

const inputCls = 'w-full rounded border border-gray-700 bg-gray-900 px-2.5 py-1.5 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none';

// ---------------------------------------------------------------------------
// Small UI atoms
// ---------------------------------------------------------------------------

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="border-b border-gray-800 px-4 py-3">
    <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">{title}</h3>
    {children}
  </div>
);

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block mb-3">
      <span className="mb-1 block text-xs text-gray-400">{label}</span>
      {children}
    </label>
  );
}

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="flex items-center gap-2 text-sm text-gray-300 mb-2 cursor-pointer">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="h-4 w-4 rounded border-gray-600 bg-gray-800" />
      {label}
    </label>
  );
}

// ---------------------------------------------------------------------------
// Canvas node
// ---------------------------------------------------------------------------

const CanvasNode: React.FC<{
  state: WorkflowState;
  x: number; y: number;
  selected: boolean;
  linkingFrom: string | null;
  warning?: string | null;
  onMouseDown: (e: React.MouseEvent, id: string) => void;
  onStartLink: (id: string) => void;
}> = ({ state, x, y, selected, linkingFrom, warning, onMouseDown, onStartLink }) => {
  const typeColor: Record<string, string> = {
    INITIAL: 'border-green-500', COMPLETED: 'border-green-500', FAILED: 'border-red-500',
    CANCELLED: 'border-gray-500', WAITING: 'border-amber-500', APPROVAL: 'border-purple-500',
    IN_PROGRESS: 'border-blue-500', NORMAL: 'border-gray-600',
  };
  return (
    <div
      data-testid="canvas-node"
      onMouseDown={(e) => onMouseDown(e, state.id)}
      className={`absolute select-none cursor-move rounded-lg border-2 bg-gray-900 shadow-lg ${selected ? 'ring-2 ring-blue-500 border-blue-400' : typeColor[state.state_type] || 'border-gray-600'}`}
      style={{ left: x, top: y, width: NODE_W, minHeight: NODE_H }}
    >
      <div className="flex items-center justify-between px-3 pt-2">
        <span className="truncate text-sm font-semibold text-gray-100" title={state.name}>{state.name}</span>
        {state.is_initial && <span className="text-[10px] text-green-400">▶ start</span>}
        {state.is_terminal && <span className="text-[10px] text-green-400">■ end</span>}
      </div>
      <div className="px-3 py-1 text-[10px] uppercase tracking-wide text-gray-500">{state.state_type.replace(/_/g, ' ')}</div>
      <div className="flex items-center gap-2 px-3 pb-2 text-[10px] text-gray-400">
        <span title="incoming transitions">↓{state.incoming_count}</span>
        <span title="outgoing transitions">↑{state.outgoing_count}</span>
        {(state.approval_config?.required || state.state_type === 'APPROVAL') && <span title="approval required" className="text-purple-400">🛡 approval</span>}
        {state.available_actions?.length ? <span title="has actions" className="text-blue-400">⚡ {state.available_actions.length}</span> : null}
        {warning && <span title={warning} className="text-amber-400">⚠</span>}
      </div>
      {linkingFrom === state.id && (
        <button
          onClick={() => onStartLink(state.id)}
          className="absolute -right-3 top-1/2 -translate-y-1/2 h-6 w-6 rounded-full bg-blue-600 text-xs text-white hover:bg-blue-500"
          title="Create transition from here"
        >→</button>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main studio page
// ---------------------------------------------------------------------------

export const WorkflowStudio: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const [graph, setGraph] = useState<StudioGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  // selection & panels
  const [selectedStateId, setSelectedStateId] = useState<string | null>(null);
  const [selectedTransitionId, setSelectedTransitionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'canvas' | 'forms' | 'versions' | 'executions'>('canvas');

  // canvas transform
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 40, y: 40 });
  const [linkingFrom, setLinkingFrom] = useState<string | null>(null);

  // bottom panel
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [simulation, setSimulation] = useState<SimulationResult | null>(null);
  const [bottomOpen, setBottomOpen] = useState(true);

  // ai modal
  const [aiOpen, setAiOpen] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiSuggestion, setAiSuggestion] = useState<AIWorkflowSuggestion | null>(null);
  const [aiBusy, setAiBusy] = useState(false);

  // simulation inputs
  const [simStart, setSimStart] = useState('');
  const [simData, setSimData] = useState('{"estimate_points": 8}');

  // versions/executions data
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);

  const canvasRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ id: string; dx: number; dy: number } | null>(null);
  const panningRef = useRef<{ x: number; y: number } | null>(null);

  // ---------------- data loading ----------------

  const load = useCallback(async () => {
    if (!workflowId) return;
    try {
      const g = await workflowApi.getStudio(workflowId);
      setGraph(g);
      setValidation(g.validation ?? null);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load workflow studio');
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  useEffect(() => { load(); }, [load]);

  // Realtime (Phase 23/24): refresh silently when workflow events arrive — no page reload.
  useRealtimeEvent('workflow.updated', useCallback(() => { load(); }, [load]));
  useRealtimeEvent('workflow.published', useCallback(() => { load(); }, [load]));
  useRealtimeEvent('workflow.archived', useCallback(() => { load(); }, [load]));
  useRealtimeEvent('workflow.execution.started', useCallback(() => { load(); }, [load]));
  useRealtimeEvent('workflow.execution.completed', useCallback(() => { load(); }, [load]));
  useRealtimeEvent('workflow.execution.failed', useCallback(() => { load(); }, [load]));

  // ---------------- canvas helpers ----------------

  const layouts = useMemo(() => {
    const map: Record<string, { x: number; y: number }> = {};
    graph?.layouts.forEach((l) => { map[l.state_id] = { x: l.x, y: l.y }; });
    // auto-layout fallback: arrange states in a horizontal flow
    graph?.states.forEach((s, i) => {
      if (!map[s.id]) map[s.id] = { x: 60 + i * (NODE_W + 80), y: 80 };
    });
    return map;
  }, [graph]);

  const statesById = useMemo(() => {
    const m: Record<string, WorkflowState> = {};
    graph?.states.forEach((s) => { m[s.id] = s; });
    return m;
  }, [graph]);

  const warningsByState = useMemo(() => {
    const m: Record<string, string> = {};
    validation?.issues.forEach((i) => {
      if (i.severity === 'ERROR' && i.entity_id) m[i.entity_id] = i.message;
      else if (i.severity === 'WARNING' && i.entity_id && !m[i.entity_id]) m[i.entity_id] = i.message;
    });
    return m;
  }, [validation]);

  const handleNodeMouseDown = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setSelectedStateId(id);
    setSelectedTransitionId(null);
    const pos = layouts[id] || { x: 0, y: 0 };
    dragRef.current = { id, dx: e.clientX - pos.x * zoom - pan.x, dy: e.clientY - pos.y * zoom - pan.y };
  };

  const handleCanvasMouseMove = (e: React.MouseEvent) => {
    if (dragRef.current && canvasRef.current) {
      const x = (e.clientX - dragRef.current.dx - pan.x) / zoom;
      const y = (e.clientY - dragRef.current.dy - pan.y) / zoom;
      setGraph((g) => g ? {
        ...g,
        layouts: g.layouts.some((l) => l.state_id === dragRef.current!.id)
          ? g.layouts.map((l) => l.state_id === dragRef.current!.id ? { ...l, x, y } : l)
          : [...g.layouts, { state_id: dragRef.current!.id, x, y }],
      } : g);
    } else if (panningRef.current) {
      setPan({
        x: pan.x + (e.clientX - panningRef.current.x),
        y: pan.y + (e.clientY - panningRef.current.y),
      });
      panningRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const stopInteractions = () => { dragRef.current = null; panningRef.current = null; };

  const fitCanvas = () => {
    if (!graph || !graph.states.length || !canvasRef.current) return;
    const xs = Object.values(layouts).map((p) => p.x);
    const ys = Object.values(layouts).map((p) => p.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs) + NODE_W;
    const minY = Math.min(...ys), maxY = Math.max(...ys) + NODE_H;
    const rect = canvasRef.current.getBoundingClientRect();
    const zx = rect.width / (maxX - minX + 120);
    const zy = rect.height / (maxY - minY + 120);
    const z = Math.max(0.3, Math.min(1.5, Math.min(zx, zy)));
    setZoom(z);
    setPan({ x: -minX * z + 60, y: -minY * z + 60 });
  };

  // ---------------- actions ----------------

  const refreshValidation = async () => {
    if (!workflowId) return;
    try {
      const v = await workflowApi.validate(workflowId);
      setValidation(v);
      setBottomOpen(true);
      setSimulation(null);
      setStatus(`Validation: ${v.status}`);
    } catch (e: any) { setError(e?.response?.data?.detail || 'Validation failed'); }
  };

  const runSimulation = async () => {
    if (!workflowId) return;
    let sample: Record<string, any> = {};
    try { sample = simData.trim() ? JSON.parse(simData) : {}; }
    catch { setError('Simulation sample data must be valid JSON'); return; }
    try {
      const s = await workflowApi.simulate(workflowId, {
        entity_type: 'TASK',
        sample_data: sample,
        start_state_id: simStart || undefined,
      });
      setSimulation(s);
      setValidation(null);
      setBottomOpen(true);
      setStatus(`Simulation: ${s.status} (dry-run)`);
    } catch (e: any) { setError(e?.response?.data?.detail || 'Simulation failed'); }
  };

  const saveDraft = async () => {
    if (!workflowId || !graph) return;
    try {
      await workflowApi.saveLayout(workflowId, graph.layouts);
      await workflowApi.createVersion(workflowId, 'Saved from studio');
      setStatus('Draft saved (new version created)');
      load();
    } catch (e: any) { setError(e?.response?.data?.detail || 'Save failed'); }
  };

  const publish = async () => {
    if (!workflowId) return;
    try {
      if (graph) await workflowApi.saveLayout(workflowId, graph.layouts);
      const res = await workflowApi.publish(workflowId);
      setStatus(`Published version ${res.status === 'published' ? '' : ''}successfully`);
      setBottomOpen(false);
      load();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail?.validation) {
        setValidation(detail.validation);
        setBottomOpen(true);
        setStatus('Publish blocked by validation errors');
      } else {
        setError(typeof detail === 'string' ? detail : 'Publish failed');
      }
    }
  };

  const archive = async () => {
    if (!workflowId) return;
    try {
      await workflowApi.archive(workflowId);
      setStatus('Workflow archived');
      load();
    } catch (e: any) { setError(e?.response?.data?.detail || 'Archive failed'); }
  };

  const resetLayout = async () => {
    if (!workflowId) return;
    try {
      const layoutsNew = await workflowApi.resetLayout(workflowId);
      setGraph((g) => (g ? { ...g, layouts: layoutsNew } : g));
      setStatus('Layout reset');
    } catch (e: any) { setError(e?.response?.data?.detail || 'Reset failed'); }
  };

  const saveLayoutOnly = async () => {
    if (!workflowId || !graph) return;
    try {
      await workflowApi.saveLayout(workflowId, graph.layouts);
      setStatus('Layout saved');
    } catch (e: any) { setError(e?.response?.data?.detail || 'Save layout failed'); }
  };

  // ---------------- AI assistant ----------------

  const runAI = async () => {
    setAiBusy(true);
    setAiSuggestion(null);
    try {
      const s = await workflowApi.generateAI(aiPrompt);
      setAiSuggestion(s);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'AI assistant failed');
    } finally { setAiBusy(false); }
  };

  const applyAI = async () => {
    if (!aiSuggestion) return;
    setAiBusy(true);
    try {
      await workflowApi.applyAISuggestion(aiSuggestion);
      setAiOpen(false);
      setAiSuggestion(null);
      setAiPrompt('');
      setStatus('AI suggestion applied as a new draft workflow (see Workflows list)');
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Apply failed');
    } finally { setAiBusy(false); }
  };

  // ---------------- state/transition mutations ----------------

  const addState = async () => {
    if (!workflowId) return;
    try {
      const n = graph?.states.length ?? 0;
      await workflowApi.createState(workflowId, { name: `New State ${n + 1}`, state_type: 'NORMAL' });
      load();
    } catch (e: any) { setError(e?.response?.data?.detail || 'Create state failed'); }
  };

  const updateSelectedState = async (patch: Record<string, any>) => {
    if (!workflowId || !selectedStateId) return;
    try {
      await workflowApi.updateState(workflowId, selectedStateId, patch);
      load();
    } catch (e: any) { setError(e?.response?.data?.detail || 'Update state failed'); }
  };

  const deleteSelectedState = async () => {
    if (!workflowId || !selectedStateId) return;
    try {
      await workflowApi.deleteState(workflowId, selectedStateId);
      setSelectedStateId(null);
      load();
    } catch (e: any) { setError(e?.response?.data?.detail || 'Delete state failed'); }
  };

  const completeLink = async (toStateId: string) => {
    if (!workflowId || !linkingFrom) return;
    try {
      await workflowApi.createTransition(workflowId, {
        name: 'New Transition', from_state_id: linkingFrom, to_state_id: toStateId,
      });
      setLinkingFrom(null);
      load();
    } catch (e: any) { setError(e?.response?.data?.detail || 'Create transition failed'); }
  };

  const updateSelectedTransition = async (patch: Record<string, any>) => {
    if (!workflowId || !selectedTransitionId) return;
    try {
      await workflowApi.updateTransition(workflowId, selectedTransitionId, patch);
      load();
    } catch (e: any) { setError(e?.response?.data?.detail || 'Update transition failed'); }
  };

  const deleteSelectedTransition = async () => {
    if (!workflowId || !selectedTransitionId) return;
    try {
      await workflowApi.deleteTransition(workflowId, selectedTransitionId);
      setSelectedTransitionId(null);
      load();
    } catch (e: any) { setError(e?.response?.data?.detail || 'Delete transition failed'); }
  };

  const loadExecutions = async () => {
    if (!workflowId) return;
    try { setExecutions(await workflowApi.listExecutions(workflowId)); }
    catch (e: any) { setError(e?.response?.data?.detail || 'Failed to load executions'); }
  };

  useEffect(() => {
    if (activeTab === 'executions') loadExecutions();
  }, [activeTab]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---------------- render ----------------

  if (loading) return <div className="p-6 text-gray-400">Loading studio…</div>;
  if (error && !graph) return <div className="p-6 text-red-300">{error}</div>;
  if (!graph) return <div className="p-6 text-gray-400">Workflow not found.</div>;

  const selectedState = selectedStateId ? statesById[selectedStateId] : null;
  const selectedTransition = graph.transitions.find((t) => t.id === selectedTransitionId) || null;
  const publishedVersion = graph.versions.find((v) => v.status === 'PUBLISHED');

  return (
    <div className="flex h-[calc(100vh-64px)] flex-col bg-gray-950 text-gray-100">
      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-800 bg-gray-900 px-4 py-2">
        <div className="flex items-center gap-3">
          <Link to="/workflows" className="text-sm text-gray-400 hover:text-white">← Workflows</Link>
          <h1 className="text-lg font-semibold">{graph.workflow.name}</h1>
          {publishedVersion && (
            <span className="rounded-full bg-green-900/50 px-2 py-0.5 text-xs text-green-300">v{publishedVersion.version_number} published</span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button onClick={refreshValidation} className="rounded border border-gray-700 px-3 py-1.5 text-sm hover:bg-gray-800">Validate</button>
          <button onClick={runSimulation} className="rounded border border-gray-700 px-3 py-1.5 text-sm hover:bg-gray-800">Simulate</button>
          <button onClick={() => setAiOpen(true)} className="rounded border border-purple-700 bg-purple-900/30 px-3 py-1.5 text-sm text-purple-200 hover:bg-purple-900/60">AI Assist</button>
          <button onClick={saveDraft} className="rounded border border-gray-700 px-3 py-1.5 text-sm hover:bg-gray-800">Save Draft</button>
          <button onClick={publish} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-500">Publish</button>
          <button onClick={archive} className="rounded border border-red-800 px-3 py-1.5 text-sm text-red-300 hover:bg-red-900/30">Archive</button>
        </div>
      </div>

      {(status || error) && (
        <div className={`px-4 py-1.5 text-sm ${error ? 'bg-red-900/40 text-red-200' : 'bg-blue-900/30 text-blue-200'}`}>
          {error || status}
          <button className="ml-3 underline" onClick={() => { setError(null); setStatus(null); }}>dismiss</button>
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        {/* Left sidebar */}
        <div className="w-52 shrink-0 overflow-y-auto border-r border-gray-800 bg-gray-900">
          <Section title="States">
            <button onClick={addState} className="mb-2 w-full rounded border border-dashed border-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-800">+ Add State</button>
            <ul className="space-y-1">
              {graph.states.map((s) => (
                <li key={s.id}>
                  <button
                    onClick={() => { setSelectedStateId(s.id); setSelectedTransitionId(null); }}
                    className={`w-full truncate rounded px-2 py-1 text-left text-sm ${selectedStateId === s.id ? 'bg-blue-900/50 text-blue-100' : 'hover:bg-gray-800'}`}
                  >
                    <span className="inline-block h-2 w-2 rounded-full mr-1.5" style={{ background: s.color || '#6b7280' }} />
                    {s.name}
                  </button>
                </li>
              ))}
            </ul>
          </Section>
          <Section title="Transitions">
            <ul className="space-y-1">
              {graph.transitions.map((t) => (
                <li key={t.id}>
                  <button
                    onClick={() => { setSelectedTransitionId(t.id); setSelectedStateId(null); }}
                    className={`w-full truncate rounded px-2 py-1 text-left text-xs ${selectedTransitionId === t.id ? 'bg-blue-900/50 text-blue-100' : 'hover:bg-gray-800'}`}
                  >
                    {t.name}{t.requires_approval ? ' 🛡' : ''}
                  </button>
                </li>
              ))}
              {!graph.transitions.length && <li className="px-2 text-xs text-gray-500">None yet</li>}
            </ul>
          </Section>
          <Section title="Views">
            {(['canvas', 'forms', 'versions', 'executions'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`mb-1 w-full rounded px-2 py-1 text-left text-sm capitalize ${activeTab === tab ? 'bg-gray-800 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
              >
                {tab === 'forms' ? `Forms (${graph.forms.length})` : tab}
              </button>
            ))}
          </Section>
          <Section title="Zoom">
            <div className="flex items-center gap-2 text-sm">
              <button onClick={() => setZoom((z) => Math.max(0.3, z - 0.1))} className="rounded border border-gray-700 px-2">−</button>
              <span className="w-12 text-center">{Math.round(zoom * 100)}%</span>
              <button onClick={() => setZoom((z) => Math.min(2, z + 0.1))} className="rounded border border-gray-700 px-2">+</button>
              <button onClick={fitCanvas} className="rounded border border-gray-700 px-2 text-xs">Fit</button>
            </div>
          </Section>
        </div>

        {/* Center */}
        <div className="relative min-w-0 flex-1">
          {activeTab === 'canvas' && (
            <div
              ref={canvasRef}
              data-testid="workflow-canvas"
              className="relative h-full w-full overflow-hidden"
              style={{
                backgroundImage: 'radial-gradient(circle, #1f2937 1px, transparent 1px)',
                backgroundSize: `${24 * zoom}px ${24 * zoom}px`,
                backgroundPosition: `${pan.x}px ${pan.y}px`,
                cursor: panningRef.current ? 'grabbing' : 'default',
              }}
              onMouseDown={(e) => { panningRef.current = { x: e.clientX, y: e.clientY }; setSelectedStateId(null); setSelectedTransitionId(null); setLinkingFrom(null); }}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={stopInteractions}
              onMouseLeave={stopInteractions}
              onWheel={(e) => { if (e.ctrlKey || e.metaKey) { e.preventDefault(); setZoom((z) => Math.max(0.3, Math.min(2, z - e.deltaY * 0.001))); } }}
            >
              <div
                className="absolute inset-0"
                style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: '0 0' }}
              >
                {/* SVG transition layer */}
                <svg className="pointer-events-none absolute" width={1} height={1} style={{ overflow: 'visible' }}>
                  <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280" />
                    </marker>
                  </defs>
                  {graph.transitions.map((t) => {
                    const from = layouts[t.from_state_id];
                    const to = layouts[t.to_state_id];
                    if (!from || !to) return null;
                    const x1 = from.x + NODE_W, y1 = from.y + NODE_H / 2;
                    const x2 = to.x, y2 = to.y + NODE_H / 2;
                    const mx = (x1 + x2) / 2;
                    const sel = selectedTransitionId === t.id;
                    return (
                      <g key={t.id} className="pointer-events-auto cursor-pointer" onClick={(e) => { e.stopPropagation(); setSelectedTransitionId(t.id); setSelectedStateId(null); }}>
                        <path d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`} fill="none" stroke={sel ? '#3b82f6' : '#4b5563'} strokeWidth={sel ? 2.5 : 1.5} markerEnd="url(#arrow)" />
                        <text x={mx} y={(y1 + y2) / 2 - 6} textAnchor="middle" fill={sel ? '#93c5fd' : '#9ca3af'} fontSize={10}>{t.name}</text>
                      </g>
                    );
                  })}
                </svg>

                {graph.states.map((s) => (
                  <CanvasNode
                    key={s.id}
                    state={s}
                    x={layouts[s.id]?.x ?? 0}
                    y={layouts[s.id]?.y ?? 0}
                    selected={selectedStateId === s.id}
                    linkingFrom={linkingFrom}
                    warning={warningsByState[s.id]}
                    onMouseDown={handleNodeMouseDown}
                    onStartLink={(id) => setLinkingFrom(linkingFrom === id ? null : id)}
                  />
                ))}
              </div>

              {/* Canvas toolbar */}
              <div className="absolute left-3 top-3 flex gap-2">
                <button onClick={(e) => { e.stopPropagation(); if (linkingFrom) setLinkingFrom(null); else { const first = graph.states[0]; if (first) { setSelectedStateId(first.id); setLinkingFrom(first.id); } } }}
                  className="rounded bg-gray-800/90 px-3 py-1 text-xs shadow hover:bg-gray-700">
                  {linkingFrom ? 'Cancel link' : 'Link mode'}
                </button>
                <button onClick={(e) => { e.stopPropagation(); saveLayoutOnly(); }} className="rounded bg-gray-800/90 px-3 py-1 text-xs shadow hover:bg-gray-700">Save layout</button>
                <button onClick={(e) => { e.stopPropagation(); resetLayout(); }} className="rounded bg-gray-800/90 px-3 py-1 text-xs shadow hover:bg-gray-700">Reset layout</button>
                <button onClick={(e) => { e.stopPropagation(); fitCanvas(); }} className="rounded bg-gray-800/90 px-3 py-1 text-xs shadow hover:bg-gray-700">Fit</button>
              </div>

              {linkingFrom && (
                <div className="absolute bottom-3 left-3 rounded bg-purple-900/80 px-3 py-1.5 text-xs text-purple-100">
                  Link mode: click the → handle on “{statesById[linkingFrom]?.name}”, then click another state to connect.
                </div>
              )}

              {/* Minimap */}
              <div className="absolute bottom-3 right-3 rounded border border-gray-700 bg-gray-900/90 p-2" data-testid="minimap">
                <div className="relative h-24 w-40">
                  {graph.states.map((s) => {
                    const p = layouts[s.id];
                    if (!p) return null;
                    const all = Object.values(layouts);
                    const maxX = Math.max(...all.map((q) => q.x)) + NODE_W || 1;
                    const maxY = Math.max(...all.map((q) => q.y)) + NODE_H || 1;
                    return (
                      <div key={s.id}
                        className={`absolute rounded-sm ${selectedStateId === s.id ? 'bg-blue-400' : 'bg-gray-500'}`}
                        style={{ left: `${(p.x / maxX) * 100}%`, top: `${(p.y / maxY) * 100}%`, width: `${(NODE_W / maxX) * 100}%`, height: `${(NODE_H / maxY) * 100}%` }}
                      />
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'forms' && <FormsTab workflowId={workflowId!} forms={graph.forms} onChanged={load} />}
          {activeTab === 'versions' && <VersionsTab versions={graph.versions} workflowId={workflowId!} onChanged={load} />}
          {activeTab === 'executions' && <ExecutionsTab executions={executions} statesById={statesById} />}
        </div>

        {/* Right sidebar */}
        <div className="w-80 shrink-0 overflow-y-auto border-l border-gray-800 bg-gray-900">
          {selectedState && (
            <StateConfigPanel
              state={selectedState}
              graph={graph}
              onUpdate={updateSelectedState}
              onDelete={deleteSelectedState}
              onStartLink={() => setLinkingFrom(selectedState.id)}
            />
          )}
          {selectedTransition && (
            <TransitionConfigPanel
              transition={selectedTransition}
              graph={graph}
              onUpdate={updateSelectedTransition}
              onDelete={deleteSelectedTransition}
            />
          )}
          {!selectedState && !selectedTransition && (
            <div className="p-4 text-sm text-gray-500">
              Select a state or transition to configure it.
              <div className="mt-3 text-xs text-gray-600">
                Canvas: drag nodes to move · drag background to pan · Ctrl+scroll to zoom · Link mode to connect states.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom panel */}
      {bottomOpen && (validation || simulation) && (
        <div className="max-h-64 shrink-0 overflow-y-auto border-t border-gray-800 bg-gray-900 px-4 py-3" data-testid="bottom-panel">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold">{validation ? 'Workflow Validation' : 'Simulation (dry-run)'}</h3>
            <button onClick={() => setBottomOpen(false)} className="text-xs text-gray-400 hover:text-white">close</button>
          </div>
          {validation && (
            <>
              <div className={`mb-2 inline-block rounded px-2 py-0.5 text-xs font-bold ${validation.status === 'PASS' ? 'bg-green-900/60 text-green-300' : validation.status === 'WARNING' ? 'bg-amber-900/60 text-amber-300' : 'bg-red-900/60 text-red-300'}`}>
                {validation.status}{validation.can_publish ? ' · can publish' : ' · publish blocked'}
              </div>
              <ul className="space-y-1 text-sm">
                {validation.issues.map((i, idx) => (
                  <li key={idx}>
                    <span className={i.severity === 'PASS' ? 'text-green-400' : i.severity === 'WARNING' ? 'text-amber-400' : 'text-red-400'}>
                      {i.severity === 'PASS' ? '✓' : i.severity === 'WARNING' ? '⚠' : '✕'}
                    </span>{' '}
                    {i.message}
                  </li>
                ))}
              </ul>
            </>
          )}
          {simulation && (
            <>
              <div className="mb-2 text-xs text-gray-400">
                {simulation.start_state} → {simulation.end_state} · {simulation.summary} · <span className="italic">dry-run, no data modified</span>
              </div>
              <ol className="space-y-2 text-sm">
                {simulation.steps.map((s) => (
                  <li key={s.step_number} className="rounded border border-gray-800 p-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{s.from_state}</span>
                      <span className="text-gray-500">→</span>
                      <span className="font-medium">{s.to_state ?? '?'}</span>
                      <span className={`ml-auto rounded px-2 py-0.5 text-xs ${s.result === 'PASS' ? 'bg-green-900/60 text-green-300' : s.result === 'BLOCKED' ? 'bg-purple-900/60 text-purple-300' : 'bg-red-900/60 text-red-300'}`}>{s.result}</span>
                    </div>
                    {s.condition_evaluations.length > 0 && (
                      <div className="mt-1 text-xs text-gray-400">
                        Conditions: {s.condition_evaluations.map((c, i) => (
                          <span key={i} className="mr-2">{c.field} {c.operator.replace(/_/g, ' ').toLowerCase()} {JSON.stringify(c.value)} → <span className={c.result ? 'text-green-400' : 'text-red-400'}>{c.result ? 'PASS' : 'FAIL'}</span></span>
                        ))}
                      </div>
                    )}
                    {s.actions.length > 0 && (
                      <div className="mt-1 text-xs text-gray-400">
                        Actions: {s.actions.map((a, i) => <span key={i} className="mr-2">{a.action_type} → {a.status}</span>)}
                      </div>
                    )}
                    {s.detail && <div className="mt-1 text-xs text-purple-300">{s.detail}</div>}
                  </li>
                ))}
              </ol>
            </>
          )}
        </div>
      )}

      {/* AI modal */}
      {aiOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setAiOpen(false)}>
          <div className="max-h-[80vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-gray-700 bg-gray-900 p-6" onClick={(e) => e.stopPropagation()} data-testid="ai-modal">
            <h2 className="mb-1 text-lg font-semibold">AI Workflow Assistant</h2>
            <p className="mb-4 rounded border border-amber-800 bg-amber-900/30 px-3 py-2 text-xs text-amber-200">
              ⚠ AI-generated suggestion — review before applying. Nothing is saved, published, or executed automatically.
            </p>
            <textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              rows={3}
              placeholder="e.g. When a task becomes overdue, move it to blocked, notify the project manager, and require approval before reopening."
              className={`${inputCls} mb-3`}
            />
            <div className="mb-4 flex gap-2">
              <button onClick={runAI} disabled={aiBusy || !aiPrompt.trim()} className="rounded bg-purple-600 px-4 py-2 text-sm text-white hover:bg-purple-500 disabled:opacity-50">
                {aiBusy ? 'Thinking…' : 'Generate Suggestion'}
              </button>
              <button onClick={() => { setAiOpen(false); setAiSuggestion(null); }} className="rounded border border-gray-700 px-4 py-2 text-sm">Close</button>
            </div>

            {aiSuggestion && (
              <div className="space-y-3 text-sm" data-testid="ai-suggestion">
                <div>
                  <h3 className="font-semibold text-gray-200">{aiSuggestion.name}</h3>
                  <p className="text-xs text-gray-400">{aiSuggestion.description}</p>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase text-gray-500">States</h4>
                  <ul className="mt-1 list-disc pl-5 text-gray-300">
                    {aiSuggestion.states.map((s: any, i: number) => <li key={i}>{s.name} <span className="text-xs text-gray-500">({s.state_type}{s.is_initial ? ', initial' : ''}{s.is_terminal ? ', terminal' : ''})</span></li>)}
                  </ul>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase text-gray-500">Transitions</h4>
                  <ul className="mt-1 list-disc pl-5 text-gray-300">
                    {aiSuggestion.transitions.map((t: any, i: number) => (
                      <li key={i}>{t.from_key} → {t.to_key} <span className="text-xs text-gray-500">“{t.name}”{t.requires_approval ? ' · approval required' : ''}{t.conditions?.length ? ` · ${t.conditions.length} condition(s)` : ''}{t.actions?.length ? ` · ${t.actions.length} action(s)` : ''}</span></li>
                    ))}
                  </ul>
                </div>
                {aiSuggestion.form_fields.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase text-gray-500">Suggested form fields</h4>
                    <ul className="mt-1 list-disc pl-5 text-gray-300">
                      {aiSuggestion.form_fields.map((f: any, i: number) => <li key={i}>{f.label} <span className="text-xs text-gray-500">({f.type})</span></li>)}
                    </ul>
                  </div>
                )}
                {aiSuggestion.notes.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase text-gray-500">Notes</h4>
                    <ul className="mt-1 list-disc pl-5 text-gray-300">
                      {aiSuggestion.notes.map((n, i) => <li key={i}>{n}</li>)}
                    </ul>
                  </div>
                )}
                <button onClick={applyAI} disabled={aiBusy} className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50">
                  {aiBusy ? 'Applying…' : 'Review done — Apply as Draft'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Right-side panels
// ---------------------------------------------------------------------------

const StateConfigPanel: React.FC<{
  state: WorkflowState;
  graph: StudioGraph;
  onUpdate: (patch: Record<string, any>) => void;
  onDelete: () => void;
  onStartLink: () => void;
}> = ({ state, graph, onUpdate, onDelete, onStartLink }) => {
  const [name, setName] = useState(state.name);
  const [description, setDescription] = useState(state.description || '');
  const [color, setColor] = useState(state.color || '#6b7280');
  const [stateType, setStateType] = useState(state.state_type);
  const [isInitial, setIsInitial] = useState(state.is_initial);
  const [isTerminal, setIsTerminal] = useState(state.is_terminal);
  const [approvalRequired, setApprovalRequired] = useState(!!state.approval_config?.required);
  const [approverType, setApproverType] = useState(state.approval_config?.approver_type || 'ROLE');
  const [orgRole, setOrgRole] = useState(state.approval_config?.organization_role || 'ADMIN');
  const [minApprovals, setMinApprovals] = useState(state.approval_config?.minimum_approvals ?? 1);
  const [timeoutHours, setTimeoutHours] = useState(state.approval_config?.timeout_hours ?? '');
  const [onReject, setOnReject] = useState(state.approval_config?.on_reject || 'BLOCK');
  const [availableActions, setAvailableActions] = useState<string>(state.available_actions?.join(', ') || '');

  useEffect(() => {
    setName(state.name); setDescription(state.description || ''); setColor(state.color || '#6b7280');
    setStateType(state.state_type); setIsInitial(state.is_initial); setIsTerminal(state.is_terminal);
    setApprovalRequired(!!state.approval_config?.required);
    setApproverType(state.approval_config?.approver_type || 'ROLE');
    setOrgRole(state.approval_config?.organization_role || 'ADMIN');
    setMinApprovals(state.approval_config?.minimum_approvals ?? 1);
    setTimeoutHours(state.approval_config?.timeout_hours ?? '');
    setOnReject(state.approval_config?.on_reject || 'BLOCK');
    setAvailableActions(state.available_actions?.join(', ') || '');
  }, [state.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const save = () => {
    onUpdate({
      name, description: description || null, color,
      state_type: stateType, is_initial: isInitial, is_terminal: isTerminal,
      approval_config: {
        required: approvalRequired, approver_type: approverType, organization_role: orgRole,
        minimum_approvals: Number(minApprovals) || 1,
        timeout_hours: timeoutHours === '' ? null : Number(timeoutHours),
        on_reject: onReject,
      },
      available_actions: availableActions.split(',').map((a) => a.trim()).filter(Boolean),
    });
  };

  return (
    <div data-testid="state-config-panel">
      <Section title={`State: ${state.name}`}>
        <FieldRow label="Name"><input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} /></FieldRow>
        <FieldRow label="Description"><textarea className={inputCls} rows={2} value={description} onChange={(e) => setDescription(e.target.value)} /></FieldRow>
        <FieldRow label="Color / status indicator">
          <div className="flex items-center gap-2">
            <input type="color" value={color} onChange={(e) => setColor(e.target.value)} className="h-8 w-10 rounded border border-gray-700 bg-gray-900" />
            <input className={inputCls} value={color} onChange={(e) => setColor(e.target.value)} />
          </div>
        </FieldRow>
        <FieldRow label="State type">
          <select className={inputCls} value={stateType} onChange={(e) => setStateType(e.target.value)}>
            {STATE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </FieldRow>
        <Toggle checked={isInitial} onChange={setIsInitial} label="Initial state" />
        <Toggle checked={isTerminal} onChange={setIsTerminal} label="Final (terminal) state" />
      </Section>
      <Section title="Approval requirements">
        <Toggle checked={approvalRequired} onChange={setApprovalRequired} label="Approval required" />
        {approvalRequired && (
          <>
            <FieldRow label="Approver type">
              <select className={inputCls} value={approverType} onChange={(e) => setApproverType(e.target.value)}>
                <option value="ROLE">Organization role</option>
                <option value="TEAM">Team</option>
                <option value="USER">Specific member</option>
              </select>
            </FieldRow>
            {approverType === 'ROLE' && (
              <FieldRow label="Organization role">
                <select className={inputCls} value={orgRole} onChange={(e) => setOrgRole(e.target.value)}>
                  {['OWNER', 'ADMIN', 'MEMBER'].map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </FieldRow>
            )}
            {approverType === 'TEAM' && (
              <FieldRow label="Team ID"><input className={inputCls} placeholder="team uuid" onChange={() => {}} /></FieldRow>
            )}
            {approverType === 'USER' && (
              <FieldRow label="Member ID"><input className={inputCls} placeholder="user uuid" onChange={() => {}} /></FieldRow>
            )}
            <FieldRow label="Minimum approval count">
              <input type="number" min={1} className={inputCls} value={minApprovals} onChange={(e) => setMinApprovals(Number(e.target.value))} />
            </FieldRow>
            <FieldRow label="Approval timeout (hours)">
              <input type="number" min={0} className={inputCls} value={timeoutHours} onChange={(e) => setTimeoutHours(e.target.value)} />
            </FieldRow>
            <FieldRow label="Reject behavior">
              <select className={inputCls} value={onReject} onChange={(e) => setOnReject(e.target.value)}>
                <option value="BLOCK">Block transition</option>
                <option value="CANCEL">Cancel execution</option>
                <option value="RETURN_TO_PREVIOUS">Return to previous state</option>
              </select>
            </FieldRow>
          </>
        )}
      </Section>
      <Section title="Available actions (automation)">
        <FieldRow label="Comma-separated action types">
          <input className={inputCls} value={availableActions} onChange={(e) => setAvailableActions(e.target.value)} placeholder="CREATE_TASK, SEND_NOTIFICATION" />
        </FieldRow>
        <p className="text-xs text-gray-500">{state.incoming_count} incoming · {state.outgoing_count} outgoing transitions</p>
      </Section>
      <div className="flex gap-2 px-4 py-3">
        <button onClick={save} className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-500">Save State</button>
        <button onClick={onStartLink} className="rounded border border-gray-700 px-3 py-1.5 text-sm hover:bg-gray-800">Connect →</button>
        <button onClick={onDelete} className="ml-auto rounded border border-red-800 px-3 py-1.5 text-sm text-red-300 hover:bg-red-900/30">Delete</button>
      </div>
    </div>
  );
};

const TransitionConfigPanel: React.FC<{
  transition: WorkflowTransition;
  graph: StudioGraph;
  onUpdate: (patch: Record<string, any>) => void;
  onDelete: () => void;
}> = ({ transition, graph, onUpdate, onDelete }) => {
  const [name, setName] = useState(transition.name);
  const [description, setDescription] = useState(transition.description || '');
  const [fromStateId, setFromStateId] = useState(transition.from_state_id);
  const [toStateId, setToStateId] = useState(transition.to_state_id);
  const [requiresApproval, setRequiresApproval] = useState(transition.requires_approval);
  const [approverType, setApproverType] = useState(transition.approval_config?.approver_type || 'ROLE');
  const [orgRole, setOrgRole] = useState(transition.approval_config?.organization_role || 'ADMIN');
  const [minApprovals, setMinApprovals] = useState(transition.approval_config?.minimum_approvals ?? 1);
  const [timeoutHours, setTimeoutHours] = useState(transition.approval_config?.timeout_hours ?? '');
  const [onReject, setOnReject] = useState(transition.approval_config?.on_reject || 'BLOCK');
  const [conditions, setConditions] = useState(transition.conditions.map((c) => ({ field: c.field, operator: c.operator, value: c.value ?? '' })));
  const [actions, setActions] = useState(transition.actions.map((a) => ({ action_type: a.action_type, configuration: a.configuration || {}, enabled: a.enabled })));

  useEffect(() => {
    setName(transition.name); setDescription(transition.description || '');
    setFromStateId(transition.from_state_id); setToStateId(transition.to_state_id);
    setRequiresApproval(transition.requires_approval);
    setApproverType(transition.approval_config?.approver_type || 'ROLE');
    setOrgRole(transition.approval_config?.organization_role || 'ADMIN');
    setMinApprovals(transition.approval_config?.minimum_approvals ?? 1);
    setTimeoutHours(transition.approval_config?.timeout_hours ?? '');
    setOnReject(transition.approval_config?.on_reject || 'BLOCK');
    setConditions(transition.conditions.map((c) => ({ field: c.field, operator: c.operator, value: c.value ?? '' })));
    setActions(transition.actions.map((a) => ({ action_type: a.action_type, configuration: a.configuration || {}, enabled: a.enabled })));
  }, [transition.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const save = () => {
    onUpdate({
      name, description: description || null, from_state_id: fromStateId, to_state_id: toStateId,
      requires_approval: requiresApproval,
      approval_config: {
        required: requiresApproval, approver_type: approverType, organization_role: orgRole,
        minimum_approvals: Number(minApprovals) || 1,
        timeout_hours: timeoutHours === '' ? null : Number(timeoutHours),
        on_reject: onReject,
      },
      conditions: conditions.filter((c) => c.field),
      actions: actions.map((a, i) => ({ ...a, position: i })),
    });
  };

  const states = graph.states;
  const nameById: Record<string, string> = {};
  states.forEach((s) => { nameById[s.id] = s.name; });

  return (
    <div data-testid="transition-config-panel">
      <Section title={`Transition: ${transition.name}`}>
        <FieldRow label="Name"><input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} /></FieldRow>
        <FieldRow label="Description"><textarea className={inputCls} rows={2} value={description} onChange={(e) => setDescription(e.target.value)} /></FieldRow>
        <FieldRow label="From state">
          <select className={inputCls} value={fromStateId} onChange={(e) => setFromStateId(e.target.value)}>
            {states.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </FieldRow>
        <FieldRow label="To state">
          <select className={inputCls} value={toStateId} onChange={(e) => setToStateId(e.target.value)}>
            {states.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </FieldRow>
      </Section>
      <Section title="Conditions (safe operators only)">
        {conditions.map((c, idx) => (
          <div key={idx} className="mb-2 rounded border border-gray-800 p-2">
            <input className={`${inputCls} mb-1`} placeholder="field (e.g. estimate_points)" value={c.field} onChange={(e) => setConditions(conditions.map((x, i) => i === idx ? { ...x, field: e.target.value } : x))} />
            <div className="flex gap-1">
              <select className={inputCls} value={c.operator} onChange={(e) => setConditions(conditions.map((x, i) => i === idx ? { ...x, operator: e.target.value } : x))}>
                {CONDITION_OPERATORS.map((op) => <option key={op} value={op}>{op}</option>)}
              </select>
              <input className={inputCls} placeholder="value" value={String(c.value ?? '')} onChange={(e) => setConditions(conditions.map((x, i) => i === idx ? { ...x, value: e.target.value } : x))} />
              <button onClick={() => setConditions(conditions.filter((_, i) => i !== idx))} className="rounded border border-gray-700 px-2 text-xs text-red-300">✕</button>
            </div>
          </div>
        ))}
        <button onClick={() => setConditions([...conditions, { field: '', operator: 'EQUALS', value: '' }])} className="w-full rounded border border-dashed border-gray-700 px-2 py-1 text-xs hover:bg-gray-800">+ Add condition</button>
      </Section>
      <Section title="Actions (execution order)">
        {actions.map((a, idx) => (
          <div key={idx} className="mb-2 rounded border border-gray-800 p-2">
            <div className="mb-1 flex items-center gap-1">
              <span className="text-xs text-gray-500">#{idx + 1}</span>
              <select className={inputCls} value={a.action_type} onChange={(e) => setActions(actions.map((x, i) => i === idx ? { ...x, action_type: e.target.value } : x))}>
                {ACTION_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              <button onClick={() => setActions(actions.filter((_, i) => i !== idx))} className="rounded border border-gray-700 px-2 text-xs text-red-300">✕</button>
            </div>
            <Toggle checked={a.enabled} onChange={(v) => setActions(actions.map((x, i) => i === idx ? { ...x, enabled: v } : x))} label="Enabled" />
            {a.action_type === 'SEND_NOTIFICATION' && (
              <input className={inputCls} placeholder="message" value={a.configuration?.message || ''} onChange={(e) => setActions(actions.map((x, i) => i === idx ? { ...x, configuration: { ...x.configuration, message: e.target.value } } : x))} />
            )}
            {a.action_type === 'CREATE_TASK' && (
              <input className={inputCls} placeholder="task title" value={a.configuration?.title || ''} onChange={(e) => setActions(actions.map((x, i) => i === idx ? { ...x, configuration: { ...x.configuration, title: e.target.value } } : x))} />
            )}
            {a.action_type === 'CREATE_AUDIT_EVENT' && (
              <input className={inputCls} placeholder="audit event_type" value={a.configuration?.event_type || ''} onChange={(e) => setActions(actions.map((x, i) => i === idx ? { ...x, configuration: { ...x.configuration, event_type: e.target.value } } : x))} />
            )}
          </div>
        ))}
        <button onClick={() => setActions([...actions, { action_type: 'SEND_NOTIFICATION', configuration: { message: '' }, enabled: true }])} className="w-full rounded border border-dashed border-gray-700 px-2 py-1 text-xs hover:bg-gray-800">+ Add action</button>
      </Section>
      <Section title="Approval requirements">
        <Toggle checked={requiresApproval} onChange={setRequiresApproval} label="Requires approval" />
        {requiresApproval && (
          <>
            <FieldRow label="Approver type">
              <select className={inputCls} value={approverType} onChange={(e) => setApproverType(e.target.value)}>
                <option value="ROLE">Organization role</option>
                <option value="TEAM">Team</option>
                <option value="USER">Specific member</option>
              </select>
            </FieldRow>
            {approverType === 'ROLE' && (
              <FieldRow label="Organization role">
                <select className={inputCls} value={orgRole} onChange={(e) => setOrgRole(e.target.value)}>
                  {['OWNER', 'ADMIN', 'MEMBER'].map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </FieldRow>
            )}
            <FieldRow label="Minimum approval count">
              <input type="number" min={1} className={inputCls} value={minApprovals} onChange={(e) => setMinApprovals(Number(e.target.value))} />
            </FieldRow>
            <FieldRow label="Approval timeout (hours)">
              <input type="number" min={0} className={inputCls} value={timeoutHours} onChange={(e) => setTimeoutHours(e.target.value)} />
            </FieldRow>
            <FieldRow label="Reject behavior">
              <select className={inputCls} value={onReject} onChange={(e) => setOnReject(e.target.value)}>
                <option value="BLOCK">Block transition</option>
                <option value="CANCEL">Cancel execution</option>
                <option value="RETURN_TO_PREVIOUS">Return to previous state</option>
              </select>
            </FieldRow>
          </>
        )}
      </Section>
      <div className="flex gap-2 px-4 py-3">
        <button onClick={save} className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-500">Save Transition</button>
        <button onClick={onDelete} className="ml-auto rounded border border-red-800 px-3 py-1.5 text-sm text-red-300 hover:bg-red-900/30">Delete</button>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------

const FormsTab: React.FC<{ workflowId: string; forms: { id: string; name: string; is_active: boolean; field_count: number }[]; onChanged: () => void }> = ({ workflowId, forms, onChanged }) => {
  const [name, setName] = useState('Intake Form');
  const [fields, setFields] = useState<FormFieldDef[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragIdx, setDragIdx] = useState<number | null>(null);

  const FIELD_TYPES = ['TEXT', 'TEXTAREA', 'NUMBER', 'DATE', 'DATETIME', 'SELECT', 'MULTI_SELECT', 'CHECKBOX', 'RADIO', 'USER', 'TEAM', 'PROJECT', 'TASK', 'CLIENT', 'FILE', 'CUSTOM_FIELD'];

  const addField = (type: string) => {
    setFields([...fields, {
      id: `field_${Date.now()}_${fields.length}`, type, label: `New ${type.toLowerCase()} field`, position: fields.length, width: 'FULL',
    }]);
  };

  const onDrop = (idx: number) => {
    if (dragIdx === null || dragIdx === idx) return;
    const copy = [...fields];
    const [moved] = copy.splice(dragIdx, 1);
    copy.splice(idx, 0, moved);
    setFields(copy.map((f, i) => ({ ...f, position: i })));
    setDragIdx(null);
  };

  const createForm = async () => {
    setBusy(true); setError(null);
    try {
      await workflowApi.createForm(workflowId, { name, fields });
      setFields([]);
      onChanged();
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      setError(typeof d === 'string' ? d : d?.message || 'Create form failed');
    } finally { setBusy(false); }
  };

  const deleteForm = async (formId: string) => {
    try { await workflowApi.deleteForm(workflowId, formId); onChanged(); }
    catch (e: any) { setError(e?.response?.data?.detail || 'Delete failed'); }
  };

  return (
    <div className="p-4" data-testid="forms-tab">
      <h2 className="mb-3 text-lg font-semibold">Workflow Forms</h2>
      {error && <div className="mb-3 rounded border border-red-800 bg-red-900/30 px-3 py-2 text-sm text-red-200">{error}</div>}

      <div className="mb-6 rounded-lg border border-gray-800 bg-gray-900 p-4">
        <h3 className="mb-3 text-sm font-semibold">New form (drag fields to reorder)</h3>
        <div className="mb-3 flex flex-wrap gap-2">
          <input className={`${inputCls} max-w-xs`} value={name} onChange={(e) => setName(e.target.value)} />
          {FIELD_TYPES.map((t) => (
            <button key={t} onClick={() => addField(t)} className="rounded border border-gray-700 px-2 py-1 text-xs hover:bg-gray-800">+ {t.replace(/_/g, ' ')}</button>
          ))}
        </div>
        <div className="space-y-2">
          {fields.map((f, idx) => (
            <div key={f.id}
              draggable onDragStart={() => setDragIdx(idx)} onDragOver={(e) => e.preventDefault()} onDrop={() => onDrop(idx)}
              className="cursor-move rounded border border-gray-700 bg-gray-950 p-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-gray-500">{idx + 1}.</span>
                <input className={`${inputCls} max-w-[180px]`} value={f.label} onChange={(e) => setFields(fields.map((x, i) => i === idx ? { ...x, label: e.target.value } : x))} />
                <span className="rounded bg-gray-800 px-2 py-0.5 text-xs">{f.type}</span>
                <label className="flex items-center gap-1 text-xs text-gray-400">
                  <input type="checkbox" checked={!!f.required} onChange={(e) => setFields(fields.map((x, i) => i === idx ? { ...x, required: e.target.checked } : x))} /> required
                </label>
                <select className={`${inputCls} max-w-[100px]`} value={f.width || 'FULL'} onChange={(e) => setFields(fields.map((x, i) => i === idx ? { ...x, width: e.target.value } : x))}>
                  <option value="FULL">Full</option><option value="HALF">Half</option><option value="THIRD">Third</option>
                </select>
                {['SELECT', 'MULTI_SELECT', 'RADIO'].includes(f.type) && (
                  <input className={`${inputCls} max-w-[220px]`} placeholder="options, comma separated" value={(f.options || []).join(', ')}
                    onChange={(e) => setFields(fields.map((x, i) => i === idx ? { ...x, options: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) } : x))} />
                )}
                <button onClick={() => setFields(fields.filter((_, i) => i !== idx))} className="ml-auto rounded border border-gray-700 px-2 text-xs text-red-300">✕</button>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-400">
                <span>Appears when:</span>
                <input className={`${inputCls} max-w-[140px]`} placeholder="field id" value={f.visibility?.field || ''}
                  onChange={(e) => setFields(fields.map((x, i) => i === idx ? { ...x, visibility: { field: e.target.value, operator: f.visibility?.operator || 'EQUALS', value: f.visibility?.value, action: 'SHOW' } } : x))} />
                <select className={`${inputCls} max-w-[160px]`} value={f.visibility?.operator || 'EQUALS'}
                  onChange={(e) => setFields(fields.map((x, i) => i === idx ? { ...x, visibility: { field: f.visibility?.field || '', operator: e.target.value, value: f.visibility?.value, action: f.visibility?.action || 'SHOW' } } : x))}>
                  {['EQUALS', 'NOT_EQUALS', 'CONTAINS', 'NOT_CONTAINS', 'GREATER_THAN', 'LESS_THAN', 'GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL', 'IS_EMPTY', 'IS_NOT_EMPTY'].map((op) => <option key={op} value={op}>{op}</option>)}
                </select>
                <input className={`${inputCls} max-w-[120px]`} placeholder="value" value={String(f.visibility?.value ?? '')}
                  onChange={(e) => setFields(fields.map((x, i) => i === idx ? { ...x, visibility: { field: f.visibility?.field || '', operator: f.visibility?.operator || 'EQUALS', value: e.target.value, action: f.visibility?.action || 'SHOW' } } : x))} />
                <select className={`${inputCls} max-w-[90px]`} value={f.visibility?.action || 'SHOW'}
                  onChange={(e) => setFields(fields.map((x, i) => i === idx ? { ...x, visibility: { field: f.visibility?.field || '', operator: f.visibility?.operator || 'EQUALS', value: f.visibility?.value, action: e.target.value as 'SHOW' | 'HIDE' } } : x))}>
                  <option value="SHOW">show</option><option value="HIDE">hide</option>
                </select>
              </div>
            </div>
          ))}
          {!fields.length && <p className="text-xs text-gray-500">Add fields above. Conditional visibility uses the safe condition engine — no code evaluation.</p>}
        </div>
        <button onClick={createForm} disabled={busy || !name.trim()} className="mt-3 rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500 disabled:opacity-50">
          {busy ? 'Saving…' : 'Create Form'}
        </button>
      </div>

      <div className="space-y-2">
        {forms.map((f) => (
          <div key={f.id} className="flex items-center justify-between rounded border border-gray-800 bg-gray-900 px-4 py-2">
            <div>
              <span className="font-medium">{f.name}</span>
              <span className="ml-2 text-xs text-gray-500">{f.field_count} fields {f.is_active ? '' : '· inactive'}</span>
            </div>
            <button onClick={() => deleteForm(f.id)} className="rounded border border-red-800 px-2 py-1 text-xs text-red-300 hover:bg-red-900/30">Delete</button>
          </div>
        ))}
        {!forms.length && <p className="text-sm text-gray-500">No forms yet for this workflow.</p>}
      </div>
    </div>
  );
};

const VersionsTab: React.FC<{ versions: WorkflowVersion[]; workflowId: string; onChanged: () => void }> = ({ versions, workflowId, onChanged }) => {
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);

  const createVersion = async () => {
    setBusy(true);
    try { await workflowApi.createVersion(workflowId, note || undefined); setNote(''); onChanged(); }
    finally { setBusy(false); }
  };

  const statusColor = (s: string) => s === 'PUBLISHED' ? 'bg-green-900/50 text-green-300' : s === 'DRAFT' ? 'bg-blue-900/50 text-blue-300' : 'bg-gray-800 text-gray-400';

  return (
    <div className="p-4" data-testid="versions-tab">
      <div className="mb-4 flex gap-2">
        <input className={`${inputCls} max-w-xs`} placeholder="Change note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
        <button onClick={createVersion} disabled={busy} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500 disabled:opacity-50">Snapshot Draft</button>
      </div>
      <div className="space-y-2">
        {versions.map((v) => (
          <div key={v.id} className="rounded border border-gray-800 bg-gray-900 px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="font-semibold">Version {v.version_number}</span>
              <span className={`rounded-full px-2 py-0.5 text-xs ${statusColor(v.status)}`}>{v.status}</span>
              <span className="ml-auto text-xs text-gray-500">
                {v.status === 'PUBLISHED' ? `Published: ${new Date(v.published_at || v.created_at).toLocaleString()}` : `Modified: ${new Date(v.updated_at).toLocaleString()}`}
              </span>
            </div>
            {v.change_note && <p className="mt-1 text-xs text-gray-400">{v.change_note}</p>}
          </div>
        ))}
        {!versions.length && <p className="text-sm text-gray-500">No versions yet. Save a draft or publish to create one.</p>}
      </div>
    </div>
  );
};

const ExecutionsTab: React.FC<{ executions: WorkflowExecution[]; statesById: Record<string, WorkflowState> }> = ({ executions, statesById }) => {
  return (
    <div className="p-4" data-testid="executions-tab">
      <h2 className="mb-3 text-lg font-semibold">Execution History</h2>
      <div className="space-y-2">
        {executions.map((e) => (
          <div key={e.id} className="rounded border border-gray-800 bg-gray-900 p-3">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="font-mono text-xs text-gray-400">{e.id.slice(0, 8)}…</span>
              <span className="rounded bg-gray-800 px-2 py-0.5 text-xs">{e.entity_type}</span>
              <span className={`rounded px-2 py-0.5 text-xs ${e.status === 'COMPLETED' ? 'bg-green-900/50 text-green-300' : e.status === 'FAILED' ? 'bg-red-900/50 text-red-300' : 'bg-blue-900/50 text-blue-300'}`}>{e.status}</span>
              <span className="text-xs text-gray-500">
                {e.current_state_id ? `at ${statesById[e.current_state_id]?.name || 'unknown'}` : 'not started'}
                {e.trigger_source ? ` · via ${e.trigger_source}` : ''}
              </span>
              <span className="ml-auto text-xs text-gray-500">
                {e.started_at ? new Date(e.started_at).toLocaleString() : ''}
                {e.duration_seconds != null ? ` · ${e.duration_seconds.toFixed(1)}s` : ''}
              </span>
            </div>
            {e.error_message && <p className="mt-1 text-xs text-red-300">{e.error_message}</p>}
            {e.events && e.events.length > 0 && (
              <div className="mt-2 border-t border-gray-800 pt-2 text-xs text-gray-400">
                {e.events.map((ev, i) => (
                  <span key={i} className="mr-3">
                    {ev.event_type === 'TRANSITION' && '↓ '}
                    {ev.event_type}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {!executions.length && <p className="text-sm text-gray-500">No executions yet. Start one from a task using the workflow engine.</p>}
      </div>
    </div>
  );
};

export default WorkflowStudio;
