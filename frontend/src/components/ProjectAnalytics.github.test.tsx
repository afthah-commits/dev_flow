import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProjectAnalytics } from './ProjectAnalytics';
import { analyticsApi } from '../lib/analyticsApi';
import { ProjectAnalyticsResponse, GitHubAnalyticsResponse } from '../types/analytics';

vi.mock('../lib/analyticsApi', () => ({
  analyticsApi: {
    getProjectAnalytics: vi.fn(),
    getGitHubAnalytics: vi.fn()
  }
}));

const mockProject = { id: 'p1', name: 'Test Project' } as any;

const baseAnalytics: ProjectAnalyticsResponse = {
  completion_rate: 50,
  total_tasks: 10,
  completed: 5,
  in_progress: 3,
  overdue: 1,
  health: { score: 80, status: 'Healthy' },
  status_distribution: [{ status: 'TODO', count: 5 }],
  priority_distribution: [{ priority: 'HIGH', count: 5 }],
  deadlines: { overdue: 1, due_today: 0, due_soon: 0, future: 4, no_deadline: 0 },
  trends: []
};

const gh = (over: Partial<GitHubAnalyticsResponse> = {}): GitHubAnalyticsResponse => ({
  recent_commits: 0, open_prs: 0, closed_prs: 0, open_issues: 0, closed_issues: 0,
  ...over
});

function setup(ghResponse: Promise<GitHubAnalyticsResponse>) {
  (analyticsApi.getProjectAnalytics as any).mockResolvedValue(baseAnalytics);
  (analyticsApi.getGitHubAnalytics as any).mockImplementation(() => ghResponse);
  render(<ProjectAnalytics project={mockProject} />);
}

describe('ProjectAnalytics GitHub section states', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows the loading state first', async () => {
    (analyticsApi.getProjectAnalytics as any).mockReturnValue(new Promise(() => {}));
    (analyticsApi.getGitHubAnalytics as any).mockReturnValue(new Promise(() => {}));
    render(<ProjectAnalytics project={mockProject} />);
    expect(screen.getByText('Loading analytics...')).toBeInTheDocument();
  });

  it('shows not-connected state', async () => {
    setup(Promise.resolve(gh({ status: 'not_connected' })));
    expect(await screen.findByText(
      /GitHub is not connected\. Connect GitHub in Settings/i
    )).toBeInTheDocument();
  });

  it('shows no-repository state', async () => {
    setup(Promise.resolve(gh({ status: 'no_repository' })));
    expect(await screen.findByText(
      /No GitHub repository is configured for this project\./i
    )).toBeInTheDocument();
  });

  it('shows successful GitHub metrics', async () => {
    setup(Promise.resolve(gh({
      status: 'ok', recent_commits: 7, open_prs: 2, open_issues: 3
    })));
    expect(await screen.findByText('Recent Commits')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('distinguishes genuine zero activity from missing connection', async () => {
    setup(Promise.resolve(gh({ status: 'ok' })));
    // With status ok and zeros, the metric rows render (real zero activity),
    // not the "not connected" fallback.
    expect(await screen.findByText('Recent Commits')).toBeInTheDocument();
    expect(screen.queryByText(/GitHub is not connected/i)).not.toBeInTheDocument();
  });

  it('shows degraded warning with retry and does not render zeros as activity', async () => {
    setup(Promise.resolve(gh({ status: 'unavailable' })));
    expect(await screen.findByText(
      /GitHub data is temporarily unavailable/i
    )).toBeInTheDocument();
    expect(screen.queryByText('Recent Commits')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('retries once on explicit click and updates the section', async () => {
    const degraded = gh({ status: 'unavailable' });
    const healthy = gh({ status: 'ok', recent_commits: 5 });
    let call = 0;
    (analyticsApi.getProjectAnalytics as any).mockResolvedValue(baseAnalytics);
    (analyticsApi.getGitHubAnalytics as any)
      .mockImplementation(() => (call++ === 0 ? Promise.resolve(degraded) : Promise.resolve(healthy)));
    render(<ProjectAnalytics project={mockProject} />);

    fireEvent.click(await screen.findByRole('button', { name: /retry/i }));
    expect(await screen.findByText('Recent Commits')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect((analyticsApi.getGitHubAnalytics as any).mock.calls.length).toBe(2);
  });

  it('keeps the rest of Project Analytics usable when GitHub degrades', async () => {
    setup(Promise.resolve(gh({ status: 'unavailable' })));
    expect(await screen.findByText('Completion Rate')).toBeInTheDocument();
    expect(screen.getByText('Task Trends (Last 7 Days)')).toBeInTheDocument();
    expect(screen.getByText('Deadlines Overview')).toBeInTheDocument();
  });

  it('handles a rejected GitHub request without crashing the page', async () => {
    setup(Promise.reject(new Error('network down')));
    expect(await screen.findByText(
      /GitHub analytics is temporarily unavailable\./i
    )).toBeInTheDocument();
    expect(screen.getByText('Completion Rate')).toBeInTheDocument();
  });
});
