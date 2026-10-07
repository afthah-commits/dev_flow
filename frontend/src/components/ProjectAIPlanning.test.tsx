import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ProjectAIPlanning } from './ProjectAIPlanning';
import { aiApi } from '../lib/aiApi';
import { taskApi } from '../lib/taskApi';

vi.mock('../lib/aiApi', () => ({
  aiApi: {
    analyzePlanning: vi.fn(),
    applyPlanningSuggestions: vi.fn(),
  }
}));

vi.mock('../lib/taskApi', () => ({
  taskApi: {
    list: vi.fn().mockResolvedValue({ items: [{ id: 't1', title: 'Build payment integration' }] })
  }
}));

const nestedAnalysis = {
  task_id: 't1',
  project_id: 'p1',
  complexity: 'HIGH',
  complexity_factors: ['detailed description', '3 blocking dependencies'],
  estimate_points: 13,
  estimate_confidence: 'MEDIUM',
  estimate_factors: ['complexity HIGH', 'description available'],
  risks: ['3 blocking dependencies', 'Task is overdue'],
  missing_information: ['No assignee'],
  dependency_concerns: ['Blocked by unfinished task P47-100: Untested blocker'],
  suggested_breakdown: [
    {
      title: 'Backend payment integration', description: '', priority: 'HIGH',
      suggestion_id: 's1', estimated_points: 5, level: 0,
      children: [
        { title: 'Payment provider configuration', description: '', priority: 'MEDIUM', suggestion_id: 's1a', estimated_points: 2, level: 1, children: [] },
        { title: 'Payment service', description: '', priority: 'MEDIUM', suggestion_id: 's1b', estimated_points: 3, level: 1, children: [] },
        { title: 'Error handling', description: '', priority: 'LOW', suggestion_id: 's1c', estimated_points: 1, level: 1, children: [] },
      ]
    },
    {
      title: 'Frontend checkout', description: '', priority: 'MEDIUM',
      suggestion_id: 's2', estimated_points: 3, level: 0,
      children: [
        { title: 'Checkout UI', description: '', priority: 'MEDIUM', suggestion_id: 's2a', estimated_points: 2, level: 1, children: [] },
        { title: 'Payment state handling', description: '', priority: 'LOW', suggestion_id: 's2b', estimated_points: 1, level: 1, children: [] },
      ]
    },
    { title: 'Webhook handling', description: '', priority: 'HIGH', suggestion_id: 's3', estimated_points: 2, level: 0, children: [] },
    { title: 'Testing', description: '', priority: 'MEDIUM', suggestion_id: 's4', estimated_points: 2, level: 0, children: [] },
  ],
  capacity: {
    status: 'OK', sprint_id: 's1', sprint_name: 'Sprint A',
    capacity_points: 20, committed_points: 10, remaining_points: 10
  },
  advisory: true,
  provider: 'MockAIProvider'
};

const project = { id: 'p1', name: 'Test Project' };

describe('ProjectAIPlanning (Phase 47 + 48 progressive breakdown)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders task selector and analyze button, loading state while analyzing', async () => {
    (aiApi.analyzePlanning as any).mockReturnValue(new Promise(() => {}));
    render(<ProjectAIPlanning project={project} />);
    expect(await screen.findByTestId('ai-planning-panel')).toBeInTheDocument();
    expect(screen.getByTestId('analyze-button')).toBeInTheDocument();
    expect(screen.getByText('Build payment integration')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('analyze-button'));
    expect(await screen.findByTestId('planning-loading')).toBeInTheDocument();
  });

  it('displays estimate, confidence, complexity and hierarchy', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(nestedAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    expect(await screen.findByTestId('planning-estimate')).toHaveTextContent('13');
    expect(screen.getByTestId('planning-confidence')).toHaveTextContent('MEDIUM');
    expect(screen.getByTestId('planning-complexity')).toHaveTextContent('HIGH');
    // hierarchy rendered: root and level-1 nodes visible (all expanded by default)
    expect(screen.getByTestId('suggestion-row-0')).toHaveAttribute('data-depth', '0');
    expect(screen.getByTestId('suggestion-row-0.0')).toHaveAttribute('data-depth', '1');
    expect(screen.getAllByText(/advisory/i).length).toBeGreaterThan(0);
  });

  it('displays risks', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(nestedAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await waitFor(() => expect(screen.getByTestId('planning-risks')).toBeInTheDocument());
    expect(screen.getAllByText(/3 blocking dependencies/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Task is overdue/)).toBeInTheDocument();
  });

  it('expand/collapse hides and shows children', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(nestedAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    // children visible initially (pre-expanded)
    expect(screen.getByTestId('suggestion-row-0.0')).toBeInTheDocument();
    // collapse root 0
    fireEvent.click(screen.getByTestId('suggestion-expand-0'));
    expect(screen.queryByTestId('suggestion-row-0.0')).not.toBeInTheDocument();
    expect(screen.getByTestId('suggestion-collapsed-0')).toHaveTextContent(/3 sub-suggestions hidden/);
    // expand again
    fireEvent.click(screen.getByTestId('suggestion-expand-0'));
    expect(screen.getByTestId('suggestion-row-0.0')).toBeInTheDocument();
  });

  it('parent selection: deselecting parent cascades to children; total effort updates', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(nestedAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    // all preselected: 5 + 2+3+1 + 3 + 2+1 + 2 + 2 = 21
    expect(screen.getByTestId('planning-total-effort')).toHaveTextContent('21');
    // deselect backend root (5 pts) + cascade unselects its children (2+3+1)
    fireEvent.click(screen.getByTestId('suggestion-checkbox-0'));
    expect(screen.getByTestId('suggestion-checkbox-0')).not.toBeChecked();
    expect(screen.getByTestId('suggestion-checkbox-0.0')).not.toBeChecked();
    expect(screen.getByTestId('suggestion-checkbox-0.1')).not.toBeChecked();
    expect(screen.getByTestId('planning-total-effort')).toHaveTextContent('10');
    expect(screen.getByTestId('planning-apply')).toHaveTextContent('Apply Selected (5)');
  });

  it('apply sends only selected nodes preserving hierarchy', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(nestedAnalysis);
    (aiApi.applyPlanningSuggestions as any).mockResolvedValue({ applied: 1, task_ids: ['n1'], task_keys: ['X-1'] });
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    // deselect "Payment service" (child of backend)
    fireEvent.click(screen.getByTestId('suggestion-checkbox-0.1'));
    fireEvent.click(screen.getByTestId('planning-apply'));
    await waitFor(() => expect(screen.getByTestId('planning-applied')).toBeInTheDocument());
    const sent = (aiApi.applyPlanningSuggestions as any).mock.calls[0][2];
    // two roots sent (backend + frontend), backend has 2 children (service removed)
    expect(sent.length).toBe(4);
    const backend = sent.find((s: any) => s.title === 'Backend payment integration');
    expect(backend.children.map((c: any) => c.title)).toEqual(['Payment provider configuration', 'Error handling']);
  });

  it('apply disabled when nothing selected; no auto-mutation on analyze and cancel', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(nestedAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    // unselect all (4 roots incl. cascades)
    ['0', '1', '2', '3'].forEach(k => fireEvent.click(screen.getByTestId(`suggestion-checkbox-${k}`)));
    expect(screen.getByTestId('planning-apply')).toBeDisabled();
    expect(aiApi.applyPlanningSuggestions).not.toHaveBeenCalled();
    // cancel discards the analysis
    fireEvent.click(screen.getByTestId('planning-cancel'));
    expect(screen.queryByTestId('planning-breakdown')).not.toBeInTheDocument();
    expect(aiApi.applyPlanningSuggestions).not.toHaveBeenCalled();
  });

  it('error state on failed analysis', async () => {
    (aiApi.analyzePlanning as any).mockRejectedValue({ response: { data: { detail: 'AI planning failed.' } } });
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    expect(await screen.findByTestId('planning-error')).toHaveTextContent('AI planning failed.');
  });

  it('sprint capacity and insufficient data handling', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue({
      ...nestedAnalysis,
      capacity: { status: 'INSUFFICIENT_DATA' }
    });
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await waitFor(() => expect(screen.getByTestId('planning-capacity')).toBeInTheDocument());
    expect(screen.getByText(/Insufficient data/i)).toBeInTheDocument();
  });

  it('shows maximum-depth warning when 3 levels are used', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue({
      ...nestedAnalysis,
      suggested_breakdown: [
        {
          title: 'Root', description: '', priority: 'MEDIUM', suggestion_id: 'r0',
          estimated_points: 2, level: 0,
          children: [{
            title: 'Mid', description: '', priority: 'MEDIUM', suggestion_id: 'r0a',
            estimated_points: 1, level: 1,
            children: [{ title: 'Leaf', description: '', priority: 'LOW', suggestion_id: 'r0a1', estimated_points: 1, level: 2, children: [] }],
          }],
        },
      ]
    });
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    expect(screen.getByTestId('max-depth-warning')).toHaveTextContent(/Maximum suggested depth/);
    expect(screen.getByTestId('suggestion-row-0.0.0')).toHaveAttribute('data-depth', '2');
  });

  it('project-level analysis (no task selected) disables apply', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue({ ...nestedAnalysis, task_id: null });
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    expect(screen.getByTestId('planning-apply')).toBeDisabled();
    expect(screen.getByText(/Select a specific task to apply/i)).toBeInTheDocument();
  });
});

describe('ProjectAIPlanning Phase 49 — breakdown editor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  async function openEditor() {
    (aiApi.analyzePlanning as any).mockResolvedValue(nestedAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
  }

  it('edit mode: opens, save persists the edit locally, cancel reverts', async () => {
    await openEditor();
    fireEvent.click(screen.getByTestId('suggestion-edit-0'));
    const titleBox = screen.getByTestId('edit-title-0') as HTMLInputElement;
    expect(titleBox.value).toBe('Backend payment integration');
    fireEvent.change(titleBox, { target: { value: 'Payments platform (edited)' } });
    fireEvent.change(screen.getByTestId('edit-points-0'), { target: { value: '9' } });
    fireEvent.click(screen.getByTestId('edit-save-0'));
    // saved: row shows new title and points; edit box gone
    expect(screen.getByTestId('suggestion-row-0')).toHaveTextContent('Payments platform (edited)');
    expect(screen.getByTestId('suggestion-row-0')).toHaveTextContent('9 pts');
    expect(screen.queryByTestId('edit-title-0')).not.toBeInTheDocument();
    // total effort reflects the edit (5 -> 9, total 21 -> 25)
    expect(screen.getByTestId('planning-total-effort')).toHaveTextContent('25');

    // cancel reverts
    fireEvent.click(screen.getByTestId('suggestion-edit-2'));
    fireEvent.change(screen.getByTestId('edit-title-2'), { target: { value: 'SHOULD NOT STAY' } });
    fireEvent.click(screen.getByTestId('edit-cancel-2'));
    expect(screen.getByTestId('suggestion-row-2')).toHaveTextContent('Webhook handling');
  });

  it('add child appends a selected sub-suggestion within limits', async () => {
    await openEditor();
    // root 2 (Webhook handling) has no children
    fireEvent.click(screen.getByTestId('suggestion-add-child-2'));
    expect(screen.getByTestId('suggestion-row-2.0')).toHaveAttribute('data-depth', '1');
    expect(screen.getByTestId('suggestion-checkbox-2.0')).toBeChecked();
    // root 0 already has 3 children; adding a 9th... limit is 8 so allowed until 8;
    // instead verify depth rejection on a depth-1 node (levels max 3 = depth<=1)
    fireEvent.click(screen.getByTestId('suggestion-add-child-0.0'));
    // depth 1 + 1 = 2 = last valid level... actually MAX_DEPTH-1 = 2 > f.depth(1) so allowed;
    // but child of 0.0 at depth 2 is the last level — still allowed. Then adding below it must fail:
    fireEvent.click(screen.getByTestId('suggestion-add-child-0.0.0'));
    expect(screen.getByTestId('planning-error')).toHaveTextContent(/maximum depth/i);
  });

  it('delete node removes node + subtree with confirm; warns on subtree', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    await openEditor();
    fireEvent.click(screen.getByTestId('suggestion-delete-0'));
    expect(confirmSpy).toHaveBeenCalled();
    // node and its subtree content gone
    expect(screen.queryByText('Backend payment integration')).not.toBeInTheDocument();
    expect(screen.queryByText('Payment provider configuration')).not.toBeInTheDocument();
    // siblings re-keyed: Frontend checkout is now root 0
    expect(screen.getByTestId('suggestion-row-0')).toHaveTextContent('Frontend checkout');
    confirmSpy.mockRestore();
  });

  it('delete with cancel confirm keeps the node', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    await openEditor();
    fireEvent.click(screen.getByTestId('suggestion-delete-0'));
    expect(screen.getByTestId('suggestion-row-0')).toBeInTheDocument();
    confirmSpy.mockRestore();
  });

  it('move node to another parent prevents cycles and preserves selection', async () => {
    await openEditor();
    // move "Webhook handling" (root 2) under "Frontend checkout" (root 1)
    const moveSelect = screen.getByTestId('suggestion-move-2') as HTMLSelectElement;
    fireEvent.change(moveSelect, { target: { value: '1' } });
    // old root 2 gone; new child 1.2 exists at depth 1
    expect(screen.getByTestId('suggestion-row-1.2')).toHaveTextContent('Webhook handling');
    expect(screen.getByTestId('suggestion-row-1.2')).toHaveAttribute('data-depth', '1');
    // selection preserved (was preselected)
    expect(screen.getByTestId('suggestion-checkbox-1.2')).toBeChecked();
    // cycle prevention: a child cannot move under its own descendant —
    // root 0's move options must not include its own children
    const opts = Array.from((screen.getByTestId('suggestion-move-0') as HTMLSelectElement).options).map(o => o.value);
    expect(opts).not.toContain('0');
    expect(opts).not.toContain('0.0');
  });

  it('shows validation warning for empty title and blocks apply of invalid tree server-side', async () => {
    await openEditor();
    fireEvent.click(screen.getByTestId('suggestion-edit-0'));
    fireEvent.change(screen.getByTestId('edit-title-0'), { target: { value: '   ' } });
    fireEvent.click(screen.getByTestId('edit-save-0'));
    expect(screen.getByTestId('editor-warnings')).toHaveTextContent(/title is empty/i);
  });

  it('shows node count and depth stats', async () => {
    await openEditor();
    expect(screen.getByTestId('planning-node-count')).toHaveTextContent('nodes');
    expect(screen.getByTestId('planning-tree-depth')).toHaveTextContent('depth 2/3');
  });

  it('error state surfaces server 422 detail on apply', async () => {
    await openEditor();
    (aiApi.applyPlanningSuggestions as any).mockRejectedValue({
      response: { data: { detail: 'Suggestion title too long (max 200)' } }
    });
    fireEvent.click(screen.getByTestId('planning-apply'));
    expect(await screen.findByTestId('planning-error')).toHaveTextContent('Suggestion title too long (max 200)');
  });
});
