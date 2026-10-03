import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ProjectGitHub } from './ProjectGitHub';
import { githubApi } from '../lib/githubApi';

vi.mock('../lib/githubApi', () => ({
  githubApi: {
    getProjectRepo: vi.fn(),
    listRepositories: vi.fn(),
    connectProjectRepo: vi.fn(),
    disconnectProjectRepo: vi.fn(),
    listBranches: vi.fn(),
    listCommits: vi.fn()
  }
}));

const mockProject = { id: 'p1', name: 'Test', status: 'ACTIVE', priority: 'HIGH', tech_stack: [], created_at: '', updated_at: '' };

describe('ProjectGitHub Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders no repository state', async () => {
    (githubApi.getProjectRepo as any).mockRejectedValue({ response: { status: 404 } });
    
    render(
      <MemoryRouter>
        <ProjectGitHub project={mockProject as any} />
      </MemoryRouter>
    );
    
    expect(await screen.findByText('No GitHub Repository Connected')).toBeInTheDocument();
  });

  it('renders repository selector', async () => {
    (githubApi.getProjectRepo as any).mockRejectedValue({ response: { status: 404 } });
    (githubApi.listRepositories as any).mockResolvedValue({ 
      items: [{ id: 1, full_name: 'test/repo', default_branch: 'main', private: false }]
    });
    
    render(
      <MemoryRouter>
        <ProjectGitHub project={mockProject as any} />
      </MemoryRouter>
    );
    
    const connectBtn = await screen.findByText('Connect Repository');
    fireEvent.click(connectBtn);
    
    expect(await screen.findByText('Select Repository')).toBeInTheDocument();
    expect(await screen.findByText('test/repo')).toBeInTheDocument();
  });

  it('renders connected repository and tabs', async () => {
    (githubApi.getProjectRepo as any).mockResolvedValue({ 
      github_full_name: 'test/repo', connected_at: new Date().toISOString()
    });
    (githubApi.listBranches as any).mockResolvedValue([
      { name: 'main', commit_sha: '1234567890', protected: true }
    ]);
    
    render(
      <MemoryRouter>
        <ProjectGitHub project={mockProject as any} />
      </MemoryRouter>
    );
    
    expect(await screen.findByText('test/repo')).toBeInTheDocument();
    
    // Switch to branches tab
    const branchTab = screen.getByText('branches');
    fireEvent.click(branchTab);
    
    expect(await screen.findByText('main')).toBeInTheDocument();
    expect(screen.getByText('Protected')).toBeInTheDocument();
  });
});
