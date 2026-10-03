import { render, screen, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import Timesheet from './Timesheet';
import { timeApi } from '../lib/timeApi';
import { projectApi } from '../lib/projectApi';
import { BrowserRouter } from 'react-router-dom';

vi.mock('../lib/timeApi', () => ({
  timeApi: {
    getMySummary: vi.fn(),
    getEntries: vi.fn(),
    startTimer: vi.fn(),
    stopTimer: vi.fn(),
    deleteEntry: vi.fn()
  }
}));

vi.mock('../lib/projectApi', () => ({
  projectApi: {
    list: vi.fn()
  }
}));

test('Timesheet renders and loads data', async () => {
  vi.mocked(timeApi.getMySummary).mockResolvedValue({
    today_hours: 2,
    week_hours: 10,
    month_hours: 40,
    tracked_hours: 100,
    billable_hours: 50,
    completed_tasks: 5
  });
  
  vi.mocked(timeApi.getEntries).mockResolvedValue({
    items: [
      {
        id: '1',
        organization_id: 'org1',
        user_id: 'user1',
        project_id: 'proj1',
        description: 'Test entry',
        started_at: '2026-10-01T10:00:00Z',
        ended_at: '2026-10-01T11:00:00Z',
        duration_seconds: 3600,
        billable: true,
        source: 'MANUAL',
        created_at: '2026-10-01T10:00:00Z'
      }
    ],
    total: 1
  });

  vi.mocked(projectApi.list).mockResolvedValue({
    items: [{ id: 'proj1', name: 'Test Project' }]
  });

  render(
    <BrowserRouter>
      <Timesheet />
    </BrowserRouter>
  );

  await waitFor(() => {
    expect(screen.getByText('2h')).toBeInTheDocument(); // Today's hours
  });

  expect(screen.getByText('Test entry')).toBeInTheDocument();
  expect(screen.getByText('1h 0m')).toBeInTheDocument();
});
