import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { AuditLogs } from './AuditLogs';
import * as OrganizationContext from '../contexts/OrganizationContext';
import { api } from '../lib/axios';

vi.mock('../lib/axios', () => ({
  api: {
    get: vi.fn(),
  },
}));

test('renders audit logs and fetches data', async () => {
  // Mock org context
  vi.spyOn(OrganizationContext, 'useOrganization').mockReturnValue({
    currentOrganization: { id: 'org-1', name: 'Test Org' },
    organizations: [],
    loading: false,
    refreshOrganizations: vi.fn(),
    setCurrentOrganization: vi.fn(),
  });

  // Mock API response
  vi.mocked(api.get).mockResolvedValueOnce({
    data: {
      items: [
        {
          id: 'evt-1',
          created_at: '2026-10-01T12:00:00Z',
          event_type: 'PROJECT_CREATED',
          entity_type: 'PROJECT',
          actor_user_id: 'user-1',
          metadata: { name: 'New Proj' }
        }
      ],
      total: 1
    }
  });

  render(<AuditLogs />);

  expect(screen.getByText('Loading audit logs...')).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.getByText('PROJECT_CREATED')).toBeInTheDocument();
  });
  
  expect(screen.getByText('PROJECT')).toBeInTheDocument();
  expect(screen.getByText('user-1')).toBeInTheDocument();
});
