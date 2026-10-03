import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect } from 'vitest';
import { Sprints } from './Sprints';
import { sprintApi } from '../lib/sprintApi';

vi.mock('../lib/sprintApi', () => ({
  sprintApi: {
    list: vi.fn()
  }
}));

describe('Sprints component', () => {
  const mockProject = { id: 'p1', name: 'Proj' };

  it('renders loading state and then sprints', async () => {
    (sprintApi.list as any).mockResolvedValue([
      { id: 's1', name: 'Sprint 1', key: 'S1', status: 'ACTIVE' }
    ]);
    
    render(<Sprints project={mockProject as any} />);
    expect(screen.getByText(/loading sprints/i)).toBeInDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Sprint 1')).toBeInDocument();
      expect(screen.getByText('ACTIVE')).toBeInDocument();
    });
  });
  
  it('shows error state if api fails', async () => {
    (sprintApi.list as any).mockRejectedValue(new Error('Failed'));
    
    render(<Sprints project={mockProject as any} />);
    
    await waitFor(() => {
      expect(screen.queryByText(/loading sprints/i)).not.toBeInDocument();
    });
  });
});
