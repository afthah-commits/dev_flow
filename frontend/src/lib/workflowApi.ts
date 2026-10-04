import { api } from './axios';

// All workflow endpoints are organization-scoped via the X-Organization-Id header.
// OrganizationContext sets it globally; this interceptor is a safety net for
// requests made before/outside the provider (e.g. tests).
function orgHeaders(orgId?: string) {
  const stored = orgId || localStorage.getItem('devflow_current_org') || undefined;
  return stored ? { 'X-Organization-Id': stored } : {};
}

api.interceptors.request.use((config) => {
  if (config.headers && !config.headers['X-Organization-Id']) {
    const orgId = localStorage.getItem('devflow_current_org');
    if (orgId) config.headers['X-Organization-Id'] = orgId;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Phase 30 — Workflow Studio types & API client
// ---------------------------------------------------------------------------

export interface WorkflowState {
  id: string;
  workflow_id: string;
  name: string;
  key: string;
  description?: string | null;
  position: number;
  color?: string | null;
  state_type: string;
  is_initial: boolean;
  is_terminal: boolean;
  approval_config?: Record<string, any> | null;
  available_actions?: string[] | null;
  incoming_count: number;
  outgoing_count: number;
}

export interface WorkflowCondition {
  id?: string;
  field: string;
  operator: string;
  value?: string | null;
  condition_type?: string;
}

export interface WorkflowAction {
  id?: string;
  action_type: string;
  configuration?: Record<string, any> | null;
  position: number;
  enabled: boolean;
}

export interface WorkflowTransition {
  id: string;
  workflow_id: string;
  name: string;
  from_state_id: string;
  to_state_id: string;
  description?: string | null;
  position: number;
  requires_approval: boolean;
  approval_config?: Record<string, any> | null;
  conditions: WorkflowCondition[];
  actions: WorkflowAction[];
}

export interface StateLayout {
  state_id: string;
  x: number;
  y: number;
}

export interface WorkflowVersion {
  id: string;
  workflow_id: string;
  version_number: number;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  change_note?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  published_at?: string | null;
  archived_at?: string | null;
}

export interface FormFieldDef {
  id: string;
  type: string;
  label: string;
  description?: string | null;
  required?: boolean;
  default_value?: any;
  placeholder?: string | null;
  position: number;
  width?: string;
  visibility?: { field: string; operator: string; value?: any; action?: 'SHOW' | 'HIDE' } | null;
  validation?: Record<string, any> | null;
  options?: string[] | null;
  custom_field_id?: string | null;
}

export interface WorkflowForm {
  id: string;
  organization_id: string;
  workflow_id?: string | null;
  name: string;
  description?: string | null;
  is_active: boolean;
  configuration?: { fields?: FormFieldDef[] } | null;
  created_at: string;
  updated_at: string;
}

export interface ValidationIssue {
  severity: 'PASS' | 'WARNING' | 'ERROR';
  code: string;
  message: string;
  entity_type?: string | null;
  entity_id?: string | null;
  entity_name?: string | null;
}

export interface ValidationResult {
  status: 'PASS' | 'WARNING' | 'ERROR';
  can_publish: boolean;
  issues: ValidationIssue[];
  checked_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  workflow_version_id?: string | null;
  entity_type: string;
  entity_id: string;
  current_state_id?: string | null;
  status: string;
  trigger_source?: string | null;
  error_message?: string | null;
  started_at: string;
  completed_at?: string | null;
  duration_seconds?: number | null;
  events?: any[];
}

export interface SimulationStep {
  step_number: number;
  from_state?: string | null;
  to_state?: string | null;
  transition_name?: string | null;
  condition_evaluations: { field: string; operator: string; value?: any; result: boolean }[];
  conditions_result?: boolean | null;
  actions: { action_type: string; status: string; detail?: string }[];
  result: 'PASS' | 'FAIL' | 'BLOCKED';
  detail?: string | null;
}

export interface SimulationResult {
  dry_run: boolean;
  entity_type: string;
  start_state?: string | null;
  end_state?: string | null;
  steps: SimulationStep[];
  status: 'PASS' | 'FAIL' | 'BLOCKED';
  summary?: string | null;
}

export interface AIWorkflowSuggestion {
  name: string;
  entity_type: string;
  description?: string | null;
  states: Record<string, any>[];
  transitions: Record<string, any>[];
  form_fields: Record<string, any>[];
  notes: string[];
  preview_only: boolean;
}

export interface StudioGraph {
  workflow: {
    id: string;
    organization_id: string;
    name: string;
    description?: string | null;
    entity_type: string;
    is_active: boolean;
    states: { id: string; name: string; key: string }[];
    transitions: { id: string; name: string }[];
  };
  states: WorkflowState[];
  transitions: WorkflowTransition[];
  layouts: StateLayout[];
  forms: { id: string; name: string; is_active: boolean; field_count: number }[];
  versions: WorkflowVersion[];
  published_version_number?: number | null;
  validation?: ValidationResult | null;
}

const baseUrl = '/workflows';

export const workflowApi = {
  // Existing (Phase 29)
  list: async (): Promise<StudioGraph['workflow'][]> => {
    const res = await api.get(baseUrl);
    return res.data;
  },
  get: async (id: string): Promise<StudioGraph['workflow']> => {
    const res = await api.get(`${baseUrl}/${id}`);
    return res.data;
  },
  create: async (data: any) => {
    const res = await api.post(baseUrl, data);
    return res.data;
  },
  remove: async (id: string) => {
    await api.delete(`${baseUrl}/${id}`);
  },

  // Studio
  getStudio: async (id: string): Promise<StudioGraph> => {
    const res = await api.get(`${baseUrl}/${id}/studio`);
    return res.data;
  },

  // States
  createState: async (workflowId: string, data: any): Promise<WorkflowState> => {
    const res = await api.post(`${baseUrl}/${workflowId}/states`, data);
    return res.data;
  },
  updateState: async (workflowId: string, stateId: string, data: any): Promise<WorkflowState> => {
    const res = await api.patch(`${baseUrl}/${workflowId}/states/${stateId}`, data);
    return res.data;
  },
  deleteState: async (workflowId: string, stateId: string) => {
    await api.delete(`${baseUrl}/${workflowId}/states/${stateId}`);
  },

  // Transitions
  createTransition: async (workflowId: string, data: any): Promise<WorkflowTransition> => {
    const res = await api.post(`${baseUrl}/${workflowId}/transitions`, data);
    return res.data;
  },
  updateTransition: async (workflowId: string, transitionId: string, data: any): Promise<WorkflowTransition> => {
    const res = await api.patch(`${baseUrl}/${workflowId}/transitions/${transitionId}`, data);
    return res.data;
  },
  deleteTransition: async (workflowId: string, transitionId: string) => {
    await api.delete(`${baseUrl}/${workflowId}/transitions/${transitionId}`);
  },

  // Layout
  saveLayout: async (workflowId: string, positions: StateLayout[]): Promise<StateLayout[]> => {
    const res = await api.post(`${baseUrl}/${workflowId}/layout`, { positions });
    return res.data;
  },
  resetLayout: async (workflowId: string): Promise<StateLayout[]> => {
    const res = await api.post(`${baseUrl}/${workflowId}/layout/reset`);
    return res.data;
  },

  // Validation / Simulation
  validate: async (workflowId: string): Promise<ValidationResult> => {
    const res = await api.post(`${baseUrl}/${workflowId}/validate`);
    return res.data;
  },
  simulate: async (workflowId: string, params: {
    entity_type?: string; sample_data?: Record<string, any>;
    start_state_id?: string; target_state_id?: string;
  }): Promise<SimulationResult> => {
    const res = await api.post(`${baseUrl}/${workflowId}/simulate`, params);
    return res.data;
  },

  // Versions / lifecycle
  listVersions: async (workflowId: string): Promise<WorkflowVersion[]> => {
    const res = await api.get(`${baseUrl}/${workflowId}/versions`);
    return res.data;
  },
  createVersion: async (workflowId: string, changeNote?: string): Promise<WorkflowVersion> => {
    const res = await api.post(`${baseUrl}/${workflowId}/versions`, { change_note: changeNote });
    return res.data;
  },
  publish: async (workflowId: string): Promise<{ status: string; validation?: ValidationResult }> => {
    const res = await api.post(`${baseUrl}/${workflowId}/publish`);
    return res.data;
  },
  archive: async (workflowId: string): Promise<{ status: string }> => {
    const res = await api.post(`${baseUrl}/${workflowId}/archive`);
    return res.data;
  },

  // Executions
  listExecutions: async (workflowId: string): Promise<WorkflowExecution[]> => {
    const res = await api.get(`${baseUrl}/${workflowId}/executions`);
    return res.data;
  },
  getExecution: async (workflowId: string, executionId: string): Promise<WorkflowExecution> => {
    const res = await api.get(`${baseUrl}/${workflowId}/executions/${executionId}`);
    return res.data;
  },

  // Forms
  listForms: async (workflowId: string): Promise<WorkflowForm[]> => {
    const res = await api.get(`${baseUrl}/${workflowId}/forms`);
    return res.data;
  },
  createForm: async (workflowId: string, data: { name: string; description?: string; fields: FormFieldDef[] }): Promise<WorkflowForm> => {
    const res = await api.post(`${baseUrl}/${workflowId}/forms`, data);
    return res.data;
  },
  updateForm: async (workflowId: string, formId: string, data: any): Promise<WorkflowForm> => {
    const res = await api.patch(`${baseUrl}/${workflowId}/forms/${formId}`, data);
    return res.data;
  },
  deleteForm: async (workflowId: string, formId: string) => {
    await api.delete(`${baseUrl}/${workflowId}/forms/${formId}`);
  },

  // Analytics
  getAnalytics: async (workflowId: string) => {
    const res = await api.get(`${baseUrl}/${workflowId}/analytics`);
    return res.data;
  },

  // AI assistant (preview only)
  generateAI: async (prompt: string): Promise<AIWorkflowSuggestion> => {
    const res = await api.post('/ai/workflows/generate', { prompt });
    return res.data;
  },
  applyAISuggestion: async (suggestion: AIWorkflowSuggestion) => {
    const res = await api.post(`${baseUrl}/ai/apply`, { suggestion });
    return res.data;
  },
};
