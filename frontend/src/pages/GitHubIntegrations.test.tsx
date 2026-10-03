import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { GitHubSettings } from './GitHubIntegrations';
import { githubApi } from '../lib/githubApi';

vi.mock('../lib/githubApi', () => ({
  githubApi: {
    getStatus: vi.fn(),
    disconnect: vi.fn(),
    connect: vi.fn()
  }
}));

describe('GitHubSettings Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders not connected state', async () => {
    (githubApi.getStatus as any).mockResolvedValue({ connected: false });
    
    render(
      <MemoryRouter>
        <GitHubSettings />
      </MemoryRouter>
    );
    
    expect(await screen.findByText('Connect GitHub')).toBeInTheDocument();
    expect(screen.getByText('Link repositories to projects.')).toBeInTheDocument();
  });

  it('renders connected state', async () => {
    (githubApi.getStatus as any).mockResolvedValue({ 
      connected: true,
      github_username: 'testoctocat',
      github_avatar_url: 'http://avatar.com/1.png'
    });
    
    render(
      <MemoryRouter>
        <GitHubSettings />
      </MemoryRouter>
    );
    
    expect(await screen.findByText('testoctocat')).toBeInTheDocument();
    expect(screen.getByText('Disconnect')).toBeInTheDocument();
  });

  it('handles disconnect', async () => {
    (githubApi.getStatus as any).mockResolvedValue({ connected: true, github_username: 'testoctocat' });
    (githubApi.disconnect as any).mockResolvedValue({ message: "Disconnected" });
    
    window.confirm = vi.fn().mockReturnValue(true);
    
    render(
      <MemoryRouter>
        <GitHubSettings />
      </MemoryRouter>
    );
    
    const disconnectBtn = await screen.findByText('Disconnect');
    fireEvent.click(disconnectBtn);
    
    expect(window.confirm).toHaveBeenCalled();
    await waitFor(() => {
      expect(githubApi.disconnect).toHaveBeenCalled();
    });
  });
});
