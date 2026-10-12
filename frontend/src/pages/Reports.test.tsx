import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Reports from './Reports';
import { reportApi } from '../lib/reportApi';
import { ReportType } from '../types/report';

vi.mock('../lib/reportApi');
vi.mock('../contexts/OrganizationContext', () => ({
  useOrganization: () => ({
    currentOrganization: { id: 'org-123', name: 'Acme Corp' },
    organizations: [{ id: 'org-123', name: 'Acme Corp' }],
    loading: false
  })
}));

describe('Reports Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(reportApi.getReports).mockReturnValue(new Promise(() => {}));

    render(
      <BrowserRouter>
        <Reports />
      </BrowserRouter>
    );

    expect(screen.getByText(/Loading organization reports/i)).toBeInTheDocument();
  });

  it('renders empty state when no reports are returned', async () => {
    vi.mocked(reportApi.getReports).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Reports />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No reports created yet/i)).toBeInTheDocument();
      expect(screen.getByText(/Create your first report/i)).toBeInTheDocument();
    });
  });

  it('renders reports list with type badges and metadata', async () => {
    vi.mocked(reportApi.getReports).mockResolvedValue([
      {
        id: 'rep-1',
        organization_id: 'org-123',
        name: 'Sprint 42 Executive Report',
        description: 'Comprehensive milestone review',
        report_type: ReportType.SPRINT_REPORT,
        configuration: {},
        created_at: '2026-03-15T00:00:00Z',
        updated_at: '2026-03-15T00:00:00Z'
      }
    ]);

    render(
      <BrowserRouter>
        <Reports />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Sprint 42 Executive Report')).toBeInTheDocument();
      expect(screen.getByText('Comprehensive milestone review')).toBeInTheDocument();
      expect(screen.getByText('SPRINT REPORT')).toBeInTheDocument();
    });
  });

  it('renders error notice and retry option when API fails', async () => {
    vi.mocked(reportApi.getReports).mockRejectedValue(new Error('Network error'));

    render(
      <BrowserRouter>
        <Reports />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
      expect(screen.getByText(/Retry/i)).toBeInTheDocument();
    });
  });
});
