import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import AICommandCenter from './AICommandCenter';
import { projectApi } from '../lib/projectApi';
import { aiApi } from '../lib/aiApi';

vi.mock('../lib/projectApi');
vi.mock('../lib/aiApi');

describe('AICommandCenter', () => {
  const mockProjects = [
    {
      id: 'p-1',
      name: 'Alpha Project',
      slug: 'alpha-project',
      status: 'Active',
      priority: 'High',
      tech_stack: ['React', 'FastAPI'],
      created_at: '2026-01-01',
      updated_at: '2026-01-02'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(projectApi.list).mockReturnValue(new Promise(() => {}));
    vi.mocked(aiApi.getOrgDailyBrief).mockReturnValue(new Promise(() => {}));

    render(
      <BrowserRouter>
        <AICommandCenter />
      </BrowserRouter>
    );

    expect(screen.getByText(/Loading Predictive AI Command Center/i)).toBeInTheDocument();
  });

  it('renders empty state when no projects are returned', async () => {
    vi.mocked(projectApi.list).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 } as any);
    vi.mocked(aiApi.getOrgDailyBrief).mockResolvedValue({
      projects_needing_attention: [],
      overdue_tasks: [],
      blocked_tasks: [],
      recommended_focus_for_today: []
    } as any);

    render(
      <BrowserRouter>
        <AICommandCenter />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No Projects Available/i)).toBeInTheDocument();
      expect(screen.getByText(/\+ Create First Project/i)).toBeInTheDocument();
    });
  });

  it('renders insights and handles paginated project response properly', async () => {
    vi.mocked(projectApi.list).mockResolvedValue({ items: mockProjects, total: 1, page: 1, page_size: 10, total_pages: 1 } as any);
    vi.mocked(aiApi.getOrgDailyBrief).mockResolvedValue({
      projects_needing_attention: [],
      overdue_tasks: [{ title: 'Task Overdue', priority: 'HIGH', reason: 'Past due', source: 'task' }],
      blocked_tasks: [],
      recommended_focus_for_today: [{ title: 'Fix blocker', priority: 'HIGH', reason: 'Blocked build', source: 'task' }]
    } as any);
    vi.mocked(aiApi.getForecast).mockResolvedValue({
      velocity: 6.5,
      remaining_tasks: 4,
      confidence: 'HIGH',
      estimated_completion_date: '2026-11-01'
    } as any);
    vi.mocked(aiApi.getRiskEngine).mockResolvedValue({
      overall_risk_score: 25,
      risks: [{ title: 'DB latency', severity: 'LOW', evidence: 'Slow queries detected' }]
    } as any);
    vi.mocked(aiApi.getSmartSprintPlan).mockResolvedValue({
      recommended_capacity_points: 30,
      suggested_tasks: ['t-1'],
      excluded_tasks: []
    } as any);
    vi.mocked(aiApi.getHealthReport).mockResolvedValue({
      project_health: 'HEALTHY',
      delivery_status: 'ON_TRACK',
      deployment_health: 'PASSING',
      executive_summary: 'All milestones are meeting velocity targets.'
    } as any);
    vi.mocked(aiApi.getTaskPriorities).mockResolvedValue([
      { task_id: 't-1', task_key: 'ALP-1', score: 85, priority_level: 'HIGH', reasons: ['High impact'] }
    ] as any);

    render(
      <BrowserRouter>
        <AICommandCenter />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Predictive AI Command Center/i)).toBeInTheDocument();
      expect(screen.getByText(/Daily Organization Engineering Brief/i)).toBeInTheDocument();
      expect(screen.getByText(/Fix blocker/i)).toBeInTheDocument();
      expect(screen.getByText(/All milestones are meeting velocity targets/i)).toBeInTheDocument();
      expect(screen.getByText(/ALP-1/i)).toBeInTheDocument();
    });

    // Test tab switching
    const planningTab = screen.getByRole('button', { name: /AI Planning & Breakdown/i });
    fireEvent.click(planningTab);
    expect(planningTab).toHaveClass('text-indigo-400');

    const assistantTab = screen.getByRole('button', { name: /AI Assistant & Actions/i });
    fireEvent.click(assistantTab);
    expect(assistantTab).toHaveClass('text-indigo-400');
  });
});
