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
    list: vi.fn().mockResolvedValue({ items: [{ id: 't1', title: 'Implement payment integration' }] })
  }
}));

const mockAnalysis = {
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
    { title: 'Payment provider configuration', description: 'Configure the provider', priority: 'HIGH' },
    { title: 'Backend payment service', description: 'Implement service', priority: 'MEDIUM' },
    { title: 'Webhook handling', description: '', priority: 'HIGH' }
  ],
  capacity: {
    status: 'OK',
    sprint_id: 's1',
    sprint_name: 'Sprint A',
    capacity_points: 20,
    committed_points: 10,
    remaining_points: 10
  },
  advisory: true,
  provider: 'MockAIProvider'
};

const project = { id: 'p1', name: 'Test Project' };

describe('ProjectAIPlanning (Phase 47)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders task selector and analyze button', async () => {
    render(<ProjectAIPlanning project={project} />);
    expect(await screen.findByTestId('ai-planning-panel')).toBeInTheDocument();
    expect(screen.getByTestId('analyze-button')).toBeInTheDocument();
    expect(screen.getByText('Implement payment integration')).toBeInTheDocument();
  });

  it('shows loading state while analyzing', async () => {
    (aiApi.analyzePlanning as any).mockReturnValue(new Promise(() => {}));
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    expect(await screen.findByTestId('planning-loading')).toBeInTheDocument();
  });

  it('displays estimate, confidence and complexity after analysis', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(mockAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    expect(await screen.findByTestId('planning-estimate')).toHaveTextContent('13');
    expect(screen.getByTestId('planning-confidence')).toHaveTextContent('MEDIUM confidence');
    expect(screen.getByTestId('planning-complexity')).toHaveTextContent('HIGH');
    expect(screen.getByTestId('planning-estimate')).toBeInTheDocument();
    const advisoryLabels = screen.getAllByText(/advisory/i);
    expect(advisoryLabels.length).toBeGreaterThan(0);
  });

  it('displays risks', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(mockAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await waitFor(() => expect(screen.getByTestId('planning-risks')).toBeInTheDocument());
    expect(screen.getAllByText(/3 blocking dependencies/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Task is overdue/)).toBeInTheDocument();
  });

  it('allows selecting and unselecting suggestions, apply sends only selected', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(mockAnalysis);
    (aiApi.applyPlanningSuggestions as any).mockResolvedValue({ applied: 1, task_ids: ['n1'], task_keys: ['P47-101'] });
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    // all pre-selected
    expect(screen.getByTestId('suggestion-checkbox-0')).toBeChecked();
    expect(screen.getByTestId('suggestion-checkbox-1')).toBeChecked();
    // unselect item 1
    fireEvent.click(screen.getByTestId('suggestion-checkbox-1'));
    expect(screen.getByTestId('suggestion-checkbox-1')).not.toBeChecked();
    fireEvent.click(screen.getByTestId('planning-apply'));
    await waitFor(() => expect(screen.getByTestId('planning-applied')).toBeInTheDocument());
    expect(aiApi.applyPlanningSuggestions).toHaveBeenCalledWith('p1', 't1', [mockAnalysis.suggested_breakdown[0], mockAnalysis.suggested_breakdown[2]]);
  });

  it('apply confirmation requires explicit click; apply disabled when nothing selected', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(mockAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    // unselect all
    fireEvent.click(screen.getByTestId('suggestion-checkbox-0'));
    fireEvent.click(screen.getByTestId('suggestion-checkbox-1'));
    fireEvent.click(screen.getByTestId('suggestion-checkbox-2'));
    expect(screen.getByTestId('planning-apply')).toBeDisabled();
    // nothing sent — no auto mutation
    expect(aiApi.applyPlanningSuggestions).not.toHaveBeenCalled();
  });

  it('cancel discards the analysis without mutating', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(mockAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    fireEvent.click(screen.getByTestId('planning-cancel'));
    expect(screen.queryByTestId('planning-breakdown')).not.toBeInTheDocument();
    expect(aiApi.applyPlanningSuggestions).not.toHaveBeenCalled();
  });

  it('shows error state on failed analysis', async () => {
    (aiApi.analyzePlanning as any).mockRejectedValue({ response: { data: { detail: 'AI planning failed.' } } });
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    expect(await screen.findByTestId('planning-error')).toHaveTextContent('AI planning failed.');
  });

  it('never mutates automatically: no apply call exactly on analyze', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue(mockAnalysis);
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    expect(aiApi.applyPlanningSuggestions).not.toHaveBeenCalled();
  });

  it('shows sprint capacity and insufficient data handling', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue({
      ...mockAnalysis,
      capacity: { status: 'INSUFFICIENT_DATA' }
    });
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await waitFor(() => expect(screen.getByTestId('planning-capacity')).toBeInTheDocument());
    expect(screen.getByText(/Insufficient data/i)).toBeInTheDocument();
  });

  it('shows project-level analysis (no task selected) disables apply', async () => {
    (aiApi.analyzePlanning as any).mockResolvedValue({ ...mockAnalysis, task_id: null });
    render(<ProjectAIPlanning project={project} />);
    fireEvent.click(screen.getByTestId('analyze-button'));
    await screen.findByTestId('planning-breakdown');
    expect(screen.getByTestId('planning-apply')).toBeDisabled();
    expect(screen.getByText(/Select a specific task to apply/i)).toBeInTheDocument();
  });
});
