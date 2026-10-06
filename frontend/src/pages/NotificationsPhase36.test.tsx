import React from 'react';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import NotificationsPage from './NotificationsPage';
import ActionCenter from './ActionCenter';
import { NotificationCenter } from '../components/NotificationCenter';
import { notificationApi } from '../lib/notificationApi';

vi.mock('../lib/notificationApi', () => ({
  notificationApi: {
    getNotifications: vi.fn(),
    getUnreadCount: vi.fn(),
    getSummary: vi.fn(),
    getActionCenter: vi.fn(),
    markRead: vi.fn(),
    markUnread: vi.fn(),
    markImportant: vi.fn(),
    markUnimportant: vi.fn(),
    markAllRead: vi.fn(),
    delete: vi.fn(),
    getPreferences: vi.fn(),
    updatePreferences: vi.fn(),
  },
}));

// useRealtimeEvent is a subscription; stub it so no WebSocket is opened.
vi.mock('../hooks/useRealtime', () => ({
  useRealtimeEvent: vi.fn(),
  useRealtimeConnection: vi.fn(() => ({ isConnected: false })),
}));

const api = notificationApi as unknown as Record<string, ReturnType<typeof vi.fn>>;

const makeNotification = (over: Record<string, unknown> = {}) => ({
  id: 'n1',
  user_id: 'u1',
  organization_id: 'o1',
  type: 'JOB_FAILURE',
  priority: 'HIGH',
  entity_type: 'JOB',
  entity_id: 'e1',
  title: 'Job Failed',
  message: 'The nightly sync job failed after 3 attempts.',
  read: false,
  action_required: true,
  important: false,
  created_at: '2026-10-05T10:00:00Z',
  read_at: null,
  ...over,
});

const wrap = (ui: React.ReactElement) => render(<MemoryRouter>{ui}</MemoryRouter>);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('NotificationsPage', () => {
  it('renders notifications with type, priority and action badges', async () => {
    api.getNotifications.mockResolvedValue([makeNotification()]);

    wrap(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Job Failed')).toBeInTheDocument();
    });
    expect(screen.getByText('The nightly sync job failed after 3 attempts.')).toBeInTheDocument();

    // scope to the notification row — the type dropdown also renders "JOB FAILURE"
    const row = screen
      .getByText('The nightly sync job failed after 3 attempts.')
      .closest('div')!.parentElement!;
    expect(within(row).getByText('HIGH')).toBeInTheDocument();
    expect(within(row).getByText('JOB FAILURE')).toBeInTheDocument();
    expect(within(row).getByText('⚡ ACTION')).toBeInTheDocument();
    expect(within(row).getByText('Read')).toBeInTheDocument();
  });

  it('requests unread-only when the Unread tab is selected (backend-driven filter)', async () => {
    api.getNotifications.mockResolvedValue([makeNotification({ read: false })]);

    wrap(<NotificationsPage />);
    await waitFor(() => expect(api.getNotifications).toHaveBeenCalled());

    api.getNotifications.mockClear();
    api.getNotifications.mockResolvedValue([]);
    fireEvent.click(screen.getByRole('button', { name: 'Unread' }));

    await waitFor(() => expect(api.getNotifications).toHaveBeenCalled());
    expect(api.getNotifications.mock.calls[0][0]).toMatchObject({ unread_only: true });
  });

  it('requests important and action-required filters from the server', async () => {
    api.getNotifications.mockResolvedValue([]);
    wrap(<NotificationsPage />);
    await waitFor(() => expect(api.getNotifications).toHaveBeenCalled());

    api.getNotifications.mockClear();
    fireEvent.click(screen.getByRole('button', { name: /Important/ }));
    await waitFor(() => expect(api.getNotifications).toHaveBeenCalled());
    expect(api.getNotifications.mock.calls[0][0]).toMatchObject({ important: true });

    api.getNotifications.mockClear();
    fireEvent.click(screen.getByRole('button', { name: /Action Required/ }));
    await waitFor(() => expect(api.getNotifications).toHaveBeenCalled());
    expect(api.getNotifications.mock.calls[0][0]).toMatchObject({ action_required: true });
  });

  it('sends the type filter and date range to the backend', async () => {
    api.getNotifications.mockResolvedValue([]);
    wrap(<NotificationsPage />);
    await waitFor(() => expect(api.getNotifications).toHaveBeenCalled());

    api.getNotifications.mockClear();
    fireEvent.change(screen.getByLabelText('Filter by type:'), {
      target: { value: 'RELEASE_PROMOTED' },
    });
    await waitFor(() => expect(api.getNotifications).toHaveBeenCalled());
    expect(api.getNotifications.mock.calls[0][0]).toMatchObject({
      notification_type: 'RELEASE_PROMOTED',
    });

    api.getNotifications.mockClear();
    fireEvent.change(screen.getByLabelText('Date from'), {
      target: { value: '2026-10-01' },
    });
    await waitFor(() => expect(api.getNotifications).toHaveBeenCalled());
    // compare against the same conversion the component performs (timezone-safe)
    expect(api.getNotifications.mock.calls[0][0].date_from)
      .toBe(new Date('2026-10-01T00:00:00').toISOString());

    api.getNotifications.mockClear();
    fireEvent.change(screen.getByLabelText('Date to'), {
      target: { value: '2026-10-05' },
    });
    await waitFor(() => expect(api.getNotifications).toHaveBeenCalled());
    const params = api.getNotifications.mock.calls[0][0];
    expect(params.date_from).toBe(new Date('2026-10-01T00:00:00').toISOString());
    expect(params.date_to).toBe(new Date('2026-10-05T23:59:59').toISOString());
  });

  it('shows an empty state when there are no notifications', async () => {
    api.getNotifications.mockResolvedValue([]);
    wrap(<NotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('No notifications')).toBeInTheDocument();
    });
    expect(screen.getByText("You're all caught up!")).toBeInTheDocument();
  });

  it('calls markAllRead', async () => {
    api.getNotifications.mockResolvedValue([makeNotification()]);
    api.markAllRead.mockResolvedValue(undefined);

    wrap(<NotificationsPage />);
    await waitFor(() => expect(screen.getByText('Job Failed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Mark all read' }));
    await waitFor(() => expect(api.markAllRead).toHaveBeenCalledTimes(1));
  });
});

describe('ActionCenter', () => {
  const items = [
    {
      id: 'a1',
      type: 'DEPLOYMENT_FAILURE',
      title: 'Deployment Failed',
      description: 'Deployment deploy-42 failed: exit 1',
      entity_type: 'DEPLOYMENT',
      entity_id: 'd1',
      priority: 'HIGH',
      created_at: '2026-10-05T09:00:00Z',
      action_url: '/infrastructure/deployments/d1',
    },
    {
      id: 'a2',
      type: 'WORKFLOW_APPROVAL',
      title: 'Workflow Approval Required',
      description: 'Pending workflow approval assigned to you',
      entity_type: 'WORKFLOW_APPROVAL',
      entity_id: 'w1',
      priority: 'URGENT',
      created_at: '2026-10-05T08:00:00Z',
      action_url: '/workflows',
    },
    {
      id: 'a3',
      type: 'DAILY_REPORT_BLOCKER',
      title: 'Daily Report Blocker',
      description: 'Report on 2026-10-05 has 2 blocker(s).',
      entity_type: 'DAILY_REPORT',
      entity_id: 'r1',
      priority: 'HIGH',
      created_at: '2026-10-04T08:00:00Z',
      action_url: '/daily-reports/blockers',
    },
  ];

  const summary = {
    unread: 4,
    important: 1,
    action_required: 3,
    pending_approvals: 1,
    failed_jobs: 2,
  };

  it('renders summary counts', async () => {
    api.getActionCenter.mockResolvedValue(items);
    api.getSummary.mockResolvedValue(summary);

    wrap(<ActionCenter />);

    await waitFor(() => {
      expect(screen.getByText('Pending Approvals')).toBeInTheDocument();
    });
    expect(screen.getByText('4')).toBeInTheDocument();   // unread
    expect(screen.getByText('3')).toBeInTheDocument();   // action required
    expect(screen.getByText('2')).toBeInTheDocument();   // failed jobs
  });

  it('groups action items by source with counts', async () => {
    api.getActionCenter.mockResolvedValue(items);
    api.getSummary.mockResolvedValue(summary);

    wrap(<ActionCenter />);

    await waitFor(() => {
      expect(screen.getByText('Workflow Approvals')).toBeInTheDocument();
    });
    expect(screen.getByText('Deployment Failures')).toBeInTheDocument();
    expect(screen.getByText('Daily Report Blockers')).toBeInTheDocument();
    expect(screen.getByText('Pending workflow approval assigned to you')).toBeInTheDocument();
    expect(screen.getByText('Deployment deploy-42 failed: exit 1')).toBeInTheDocument();
  });

  it('shows an all-clear empty state', async () => {
    api.getActionCenter.mockResolvedValue([]);
    api.getSummary.mockResolvedValue({
      unread: 0, important: 0, action_required: 0, pending_approvals: 0, failed_jobs: 0,
    });

    wrap(<ActionCenter />);

    await waitFor(() => {
      expect(screen.getByText('All clear!')).toBeInTheDocument();
    });
  });
});

describe('NotificationCenter badge', () => {
  it('shows the unread badge count', async () => {
    api.getUnreadCount.mockResolvedValue({ count: 7 });
    api.getNotifications.mockResolvedValue([]);

    wrap(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.getByText('7')).toBeInTheDocument();
    });
  });

  it('renders the dropdown with notifications once opened', async () => {
    api.getUnreadCount.mockResolvedValue({ count: 1 });
    api.getNotifications.mockResolvedValue([
      makeNotification({ title: 'Release Approval Required', important: true }),
    ]);

    wrap(<NotificationCenter />);
    await waitFor(() => expect(api.getUnreadCount).toHaveBeenCalled());

    fireEvent.click(screen.getByLabelText('Open notifications'));

    await waitFor(() => {
      expect(screen.getByText('Release Approval Required')).toBeInTheDocument();
    });
    expect(api.getNotifications).toHaveBeenCalled();
    // dropdown links into the full page and action center
    expect(screen.getByText('All notifications →')).toBeInTheDocument();
    expect(screen.getByText('⚡ Action Center')).toBeInTheDocument();
  });
});
