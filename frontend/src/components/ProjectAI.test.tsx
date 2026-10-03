import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ProjectAI } from './ProjectAI';
import { aiApi } from '../lib/aiApi';

vi.mock('../lib/aiApi', () => ({
  aiApi: {
    listConversations: vi.fn(),
    createConversation: vi.fn(),
    getConversation: vi.fn(),
    sendMessage: vi.fn(),
    suggestTask: vi.fn()
  }
}));

const mockProject = { id: 'p1', name: 'Test Project', status: 'ACTIVE', priority: 'HIGH', tech_stack: [], created_at: '', updated_at: '' };
const mockConv = { id: 'c1', user_id: 'u1', project_id: 'p1', title: 'Test Chat', created_at: new Date().toISOString() };

describe('ProjectAI Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it('renders empty state and loads conversations', async () => {
    (aiApi.listConversations as any).mockResolvedValue([]);
    
    render(
      <MemoryRouter>
        <ProjectAI project={mockProject as any} />
      </MemoryRouter>
    );
    
    expect(await screen.findByText(/I am DevFlow AI/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask the AI assistant...')).toBeInTheDocument();
  });

  it('handles sending a message', async () => {
    (aiApi.listConversations as any).mockResolvedValue([mockConv]);
    (aiApi.getConversation as any).mockResolvedValue({ ...mockConv, messages: [] });
    (aiApi.sendMessage as any).mockResolvedValue({
      id: 'm1', role: 'assistant', content: 'This is an AI response'
    });
    
    render(
      <MemoryRouter>
        <ProjectAI project={mockProject as any} />
      </MemoryRouter>
    );
    
    const input = await screen.findByPlaceholderText('Ask the AI assistant...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    
    const sendBtn = screen.getByText('Send');
    fireEvent.click(sendBtn);
    
    expect(await screen.findByText('This is an AI response')).toBeInTheDocument();
  });

  it('handles task generation action', async () => {
    (aiApi.listConversations as any).mockResolvedValue([mockConv]);
    (aiApi.getConversation as any).mockResolvedValue({ ...mockConv, messages: [] });
    (aiApi.suggestTask as any).mockResolvedValue({
      structured_data: { title: 'New Task', description: 'desc', priority: 'HIGH', labels: [] }
    });
    
    window.prompt = vi.fn().mockReturnValue('Create login');
    
    render(
      <MemoryRouter>
        <ProjectAI project={mockProject as any} />
      </MemoryRouter>
    );
    
    const taskBtn = await screen.findByText('Generate Task (AI)');
    fireEvent.click(taskBtn);
    
    expect(await screen.findByText(/AI Task Suggestion/)).toBeInTheDocument();
  });
});
