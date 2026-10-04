import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { workflowApi, WorkflowForm as WorkflowFormType, FormFieldDef } from '../lib/workflowApi';

const inputCls = 'w-full rounded border border-gray-700 bg-gray-900 px-2.5 py-1.5 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none';

const FIELD_TYPES = [
  'TEXT', 'TEXTAREA', 'NUMBER', 'DATE', 'DATETIME', 'SELECT', 'MULTI_SELECT',
  'CHECKBOX', 'RADIO', 'USER', 'TEAM', 'PROJECT', 'TASK', 'CLIENT', 'FILE', 'CUSTOM_FIELD',
];
const OPERATORS = ['EQUALS', 'NOT_EQUALS', 'CONTAINS', 'NOT_CONTAINS', 'GREATER_THAN', 'LESS_THAN', 'GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL', 'IS_EMPTY', 'IS_NOT_EMPTY'];

export const WorkflowFormBuilder: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const [forms, setForms] = useState<WorkflowFormType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  // new form builder state
  const [name, setName] = useState('New Form');
  const [fields, setFields] = useState<FormFieldDef[]>([]);
  const [dragIdx, setDragIdx] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  // editing existing form
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editFields, setEditFields] = useState<FormFieldDef[]>([]);

  const load = useCallback(async () => {
    if (!workflowId) return;
    try { setForms(await workflowApi.listForms(workflowId)); }
    catch (e: any) { setError(e?.response?.data?.detail || 'Failed to load forms'); }
    finally { setLoading(false); }
  }, [workflowId]);

  useEffect(() => { load(); }, [load]);

  const addField = (type: string) => {
    setFields([...fields, {
      id: `field_${Date.now()}_${fields.length}`,
      type, label: `New ${type.toLowerCase()} field`, position: fields.length, width: 'FULL',
    }]);
  };

  const moveField = (from: number, to: number) => {
    const copy = [...fields];
    const [moved] = copy.splice(from, 1);
    copy.splice(to, 0, moved);
    setFields(copy.map((f, i) => ({ ...f, position: i })));
  };

  const createForm = async () => {
    setBusy(true); setError(null);
    try {
      await workflowApi.createForm(workflowId!, { name, fields });
      setFields([]);
      setStatus('Form created');
      load();
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      setError(typeof d === 'string' ? d : d?.message || 'Create failed');
    } finally { setBusy(false); }
  };

  const startEdit = (f: WorkflowFormType) => {
    setEditingId(f.id);
    setEditFields((f.configuration?.fields || []).map((x, i) => ({ ...x, position: i })));
  };

  const saveEdit = async () => {
    if (!editingId) return;
    setBusy(true); setError(null);
    try {
      await workflowApi.updateForm(workflowId!, editingId, { fields: editFields });
      setEditingId(null);
      setStatus('Form updated');
      load();
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      setError(typeof d === 'string' ? d : d?.message || 'Update failed');
    } finally { setBusy(false); }
  };

  const removeForm = async (formId: string) => {
    try { await workflowApi.deleteForm(workflowId!, formId); load(); }
    catch (e: any) { setError(e?.response?.data?.detail || 'Delete failed'); }
  };

  const renderFieldRow = (
    f: FormFieldDef, idx: number,
    list: FormFieldDef[], setList: (updater: (prev: FormFieldDef[]) => FormFieldDef[]) => void,
    onRemove: () => void,
  ) => (
    <div
      key={f.id}
      draggable
      onDragStart={() => setDragIdx(idx)}
      onDragOver={(e) => e.preventDefault()}
      onDrop={() => { if (dragIdx !== null) { moveField(dragIdx, idx); setDragIdx(null); } }}
      className="cursor-move rounded border border-gray-700 bg-gray-950 p-2"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-gray-500">{idx + 1}.</span>
        <input className={`${inputCls} max-w-[180px]`} value={f.label}
          onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, label: e.target.value } : x))} />
        <select className={`${inputCls} max-w-[130px]`} value={f.type}
          onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, type: e.target.value } : x))}>
          {FIELD_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <label className="flex items-center gap-1 text-xs text-gray-400">
          <input type="checkbox" checked={!!f.required}
            onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, required: e.target.checked } : x))} /> required
        </label>
        <input className={`${inputCls} max-w-[130px]`} placeholder="default value" value={String(f.default_value ?? '')}
          onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, default_value: e.target.value } : x))} />
        <input className={`${inputCls} max-w-[130px]`} placeholder="placeholder" value={f.placeholder || ''}
          onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, placeholder: e.target.value } : x))} />
        <select className={`${inputCls} max-w-[90px]`} value={f.width || 'FULL'}
          onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, width: e.target.value } : x))}>
          <option value="FULL">Full</option><option value="HALF">Half</option><option value="THIRD">Third</option>
        </select>
        <button onClick={onRemove} className="ml-auto rounded border border-gray-700 px-2 text-xs text-red-300">✕</button>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-400">
        <span>Visibility:</span>
        <input className={`${inputCls} max-w-[140px]`} placeholder="field id" value={f.visibility?.field || ''}
          onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, visibility: { field: e.target.value, operator: f.visibility?.operator || 'EQUALS', value: f.visibility?.value, action: f.visibility?.action || 'SHOW' } } : x))} />
        <select className={`${inputCls} max-w-[160px]`} value={f.visibility?.operator || 'EQUALS'}
          onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, visibility: { field: f.visibility?.field || '', operator: e.target.value, value: f.visibility?.value, action: f.visibility?.action || 'SHOW' } } : x))}>
          {OPERATORS.map((op) => <option key={op} value={op}>{op}</option>)}
        </select>
        <input className={`${inputCls} max-w-[110px]`} placeholder="value" value={String(f.visibility?.value ?? '')}
          onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, visibility: { field: f.visibility?.field || '', operator: f.visibility?.operator || 'EQUALS', value: e.target.value, action: f.visibility?.action || 'SHOW' } } : x))} />
        <select className={`${inputCls} max-w-[85px]`} value={f.visibility?.action || 'SHOW'}
          onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, visibility: { ...(f.visibility || { field: '', operator: 'EQUALS' }), action: e.target.value as 'SHOW' | 'HIDE' } } : x))}>
          <option value="SHOW">show</option><option value="HIDE">hide</option>
        </select>
        {['SELECT', 'MULTI_SELECT', 'RADIO'].includes(f.type) && (
          <input className={`${inputCls} max-w-[220px]`} placeholder="options, comma separated" value={(f.options || []).join(', ')}
            onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, options: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) } : x))} />
        )}
      </div>
      {editingId === null && f.type === 'CUSTOM_FIELD' && (
        <div className="mt-2 text-xs text-gray-400">
          Custom Field ID: <input className={`${inputCls} max-w-[260px]`} placeholder="link an existing custom field"
            value={f.custom_field_id || ''}
            onChange={(e) => setList((prev) => prev.map((x, i) => i === idx ? { ...x, custom_field_id: e.target.value || null } : x))} />
        </div>
      )}
    </div>
  );

  return (
    <div className="p-6 max-w-5xl mx-auto" data-testid="workflow-form-builder">
      <div className="mb-4 flex items-center gap-3">
        <Link to={`/workflows/${workflowId}/studio`} className="text-sm text-gray-400 hover:text-white">← Studio</Link>
        <h1 className="text-2xl font-bold text-white">Form Builder</h1>
      </div>

      {error && <div className="mb-3 rounded border border-red-800 bg-red-900/30 px-3 py-2 text-sm text-red-200">{error}</div>}
      {status && <div className="mb-3 rounded border border-green-800 bg-green-900/30 px-3 py-2 text-sm text-green-200">{status}</div>}

      <div className="mb-6 rounded-lg border border-gray-800 bg-gray-900 p-4">
        <h2 className="mb-3 text-sm font-semibold">Create form — drag to reorder fields</h2>
        <div className="mb-3 flex flex-wrap gap-2">
          <input className={`${inputCls} max-w-xs`} value={name} onChange={(e) => setName(e.target.value)} />
          {FIELD_TYPES.map((t) => (
            <button key={t} onClick={() => addField(t)} className="rounded border border-gray-700 px-2 py-1 text-xs hover:bg-gray-800">+ {t.replace(/_/g, ' ')}</button>
          ))}
        </div>
        <div className="space-y-2">
          {fields.map((f, idx) => renderFieldRow(f, idx, fields, setFields, () => setFields(fields.filter((_, i) => i !== idx))))}
          {!fields.length && <p className="text-xs text-gray-500">Add fields above. Conditional visibility uses the safe condition engine — never eval().</p>}
        </div>
        <button onClick={createForm} disabled={busy || !name.trim()} className="mt-3 rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500 disabled:opacity-50">
          {busy ? 'Saving…' : 'Create Form'}
        </button>
      </div>

      {loading ? <div className="text-gray-400 text-sm">Loading…</div> : (
        <div className="space-y-3">
          {forms.map((f) => (
            <div key={f.id} className="rounded-lg border border-gray-800 bg-gray-900 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{f.name}</h3>
                  <p className="text-xs text-gray-500">{(f.configuration?.fields || []).length} fields · updated {new Date(f.updated_at).toLocaleString()}</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => startEdit(f)} className="rounded border border-gray-700 px-3 py-1 text-xs hover:bg-gray-800">Edit fields</button>
                  <button onClick={() => removeForm(f.id)} className="rounded border border-red-800 px-3 py-1 text-xs text-red-300 hover:bg-red-900/30">Delete</button>
                </div>
              </div>
              {editingId === f.id && (
                <div className="mt-3 space-y-2 border-t border-gray-800 pt-3">
                  {editFields.map((ef, idx) => renderFieldRow(ef, idx, editFields, setEditFields, () => setEditFields(editFields.filter((_, i) => i !== idx))))}
                  {!editFields.length && <p className="text-xs text-gray-500">No fields configured yet.</p>}
                  <div className="flex gap-2">
                    <button onClick={saveEdit} disabled={busy} className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-500">Save Changes</button>
                    <button onClick={() => setEditingId(null)} className="rounded border border-gray-700 px-3 py-1.5 text-sm">Cancel</button>
                  </div>
                </div>
              )}
            </div>
          ))}
          {!forms.length && <div className="rounded border border-dashed border-gray-700 p-8 text-center text-gray-400">No forms yet.</div>}
        </div>
      )}
    </div>
  );
};

export default WorkflowFormBuilder;
