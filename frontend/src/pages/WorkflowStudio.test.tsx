/// <reference types="@testing-library/jest-dom" />
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import { WorkflowStudio } from './WorkflowStudio';
import { Workflows } from './Workflows';
import { workflowApi } from '../lib/workflowApi';

vi.mock('../lib/workflowApi', () => ({
  workflowApi: {
    getStudio: vi.fn(),
    validate: vi.fn(),
    simulate: vi.fn(),
    createState: vi.fn(),
    updateState: vi.fn(),
    deleteState: vi.fn(),
    createTransition: vi.fn(),
    updateTransition: vi.fn(),
    deleteTransition: vi.fn(),
    saveLayout: vi.fn().mockResolvedValue([]),
    resetLayout: vi.fn().mockResolvedValue([]),
    createVersion: vi.fn(),
    publish: vi.fn(),
    archive: vi.fn(),
    listExecutions: vi.fn().mockResolvedValue([]),
    listForms: vi.fn().mockResolvedValue([]),
    createForm: vi.fn(),
    updateForm: vi.fn(),
    deleteForm: vi.fn(),
    list: vi.fn().mockResolvedValue([]),
    generateAI: vi.fn(),
    applyAISuggestion: vi.fn(),
    getAnalytics: vi.fn(),
  },
}));

vi.mock('../hooks/useRealtime', () => ({
  useRealtimeEvent: vi.fn(),
  useRealtimeConnection: vi.fn(() => ({ isConnected: true })),
}));

vi.mock('../contexts/OrganizationContext', () => ({
  useOrganization: () => ({ currentOrganization: { id: 'org-1', name: 'Test Org' }, organizations: [] }),
  OrganizationProvider: ({ children }: { children: any }) => children,
}));

const mockGraph = {
  workflow: {
    id: 'wf-1', organization_id: 'org-1', name: 'Bug Triage',
    description: null, entity_type: 'TASK', is_active: true,
    states: [], transitions: [],
  },
  states: [
    {
      id: 's1', workflow_id: 'wf-1', name: 'To Do', key: 'TODO', position: 0,
      color: '#6b7280', state_type: 'INITIAL', is_initial: true, is_terminal: false,
      approval_config: null, available_actions: null, incoming_count: 0, outgoing_count: 1,
    },
    {
      id: 's2', workflow_id: 'wf-1', name: 'Done', key: 'DONE', position: 1,
      color: '#22c55e', state_type: 'COMPLETED', is_initial: false, is_terminal: true,
      approval_config: { required: true, approver_type: 'ROLE', organization_role: 'ADMIN', minimum_approvals: 1 },
      available_actions: null, incoming_count: 1, outgoing_count: 0,
    },
  ],
  transitions: [
    {
      id: 't1', workflow_id: 'wf-1', name: 'Finish', from_state_id: 's1', to_state_id: 's2',
      description: null, position: 0, requires_approval: false,
      approval_config: null, conditions: [], actions: [],
    },
  ],
  layouts: [
    { state_id: 's1', x: 60, y: 80 },
    { state_id: 's2', x: 320, y: 80 },
  ],
  forms: [],
  versions: [
    {
      id: 'v1', workflow_id: 'wf-1', version_number: 1, status: 'PUBLISHED' as const,
      change_note: null, created_by: null, created_at: '2026-10-04T00:00:00Z',
      updated_at: '2026-10-04T00:00:00Z', published_at: '2026-10-04T00:00:00Z', archived_at: null,
    },
  ],
  published_version_number: 1,
  validation: {
    status: 'WARNING',
    can_publish: true,
    checked_at: '2026-10-04T00:00:00Z',
    issues: [
      { severity: 'PASS' as const, code: 'INITIAL_STATE', message: 'Initial state configured: "To Do"' },
      { severity: 'WARNING' as const, code: 'DEAD_END_STATE', message: 'State "Done" is a dead end: no outgoing transitions and not final' },
    ],
  },
};

describe('WorkflowStudio', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (workflowApi.getStudio as ReturnType<typeof vi.fn>).mockResolvedValue(mockGraph);
    (workflowApi.listExecutions as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  });

  it('renders canvas with state nodes and transitions', async () => {
    render(
      <MemoryRouter initialEntries={['/workflows/wf-1/studio']}>
        <Routes>
          <Route path="/workflows/:workflowId/studio" element={<WorkflowStudio />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByTestId('workflow-canvas')).toBeInTheDocument());
    expect(screen.getAllByTestId('canvas-node').length).toBe(2);
    expect(screen.getByText('Bug Triage')).toBeInTheDocument();
    expect(screen.getByText('v1 published')).toBeInTheDocument();
  });

  it('shows validation warnings in the bottom panel', async () => {
    render(
      <MemoryRouter initialEntries={['/workflows/wf-1/studio']}>
        <Routes>
          <Route path="/workflows/:workflowId/studio" element={<WorkflowStudio />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByTestId('bottom-panel')).toBeInTheDocument());
    expect(screen.getByText(/Workflow Validation/i)).toBeInTheDocument();
    expect(screen.getByText(/Initial state configured/i)).toBeInTheDocument();
    expect(screen.getByText(/dead end/i)).toBeInTheDocument();
  });

  it('displays the published version badge', async () => {
    render(
      <MemoryRouter initialEntries={['/workflows/wf-1/studio']}>
        <Routes>
          <Route path="/workflows/:workflowId/studio" element={<WorkflowStudio />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('v1 published')).toBeInTheDocument());
  });

  it('versions tab lists version history', async () => {
    render(
      <MemoryRouter initialEntries={['/workflows/wf-1/studio']}>
        <Routes>
          <Route path="/workflows/:workflowId/studio" element={<WorkflowStudio />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByTestId('workflow-canvas')).toBeInTheDocument());
    const versionsButton = screen.getAllByText('versions')[0];
    versionsButton.click();
    await waitFor(() => expect(screen.getByTestId('versions-tab')).toBeInTheDocument());
    expect(screen.getByText(/Version 1/)).toBeInTheDocument();
  });
});

describe('Workflows list', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders workflow cards from the API', async () => {
    (workflowApi.list as ReturnType<typeof vi.fn>).mockResolvedValue([
      {
        id: 'wf-1', name: 'Bug Triage', description: 'Triage process',
        entity_type: 'TASK', is_active: true,
        states: [{ id: 's1', name: 'To Do', key: 'TODO' }],
        transitions: [{ id: 't1', name: 'Finish' }],
      },
    ]);
    render(
      <MemoryRouter>
        <Workflows />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('Bug Triage')).toBeInTheDocument());
    expect(screen.getByText(/1 states/)).toBeInTheDocument();
    expect(screen.getByText(/Open Studio/)).toBeInTheDocument();
  });
});
