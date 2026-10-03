/// <reference types="@testing-library/jest-dom" />
import React from "react";
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Projects from './Projects'
import Dashboard from './Dashboard'
import { projectApi } from '../lib/projectApi'
import { ProjectStatus, ProjectPriority } from '../types/project'
import { AuthProvider } from '../hooks/useAuth'

// Mock API
vi.mock('../lib/projectApi', () => ({
  projectApi: {
    list: vi.fn(),
    delete: vi.fn(),
  }
}))

// Mock Auth
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { name: 'Test User' },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn()
  }),
  AuthProvider: ({ children }: any) => <div>{children}</div>
}))

const mockProjects = [
  {
    id: '1', owner_id: 'owner1', name: 'Alpha', slug: 'alpha', 
    status: ProjectStatus.ACTIVE, priority: ProjectPriority.HIGH, 
    tech_stack: ['React'], created_at: '2023-01-01', updated_at: '2023-01-01'
  },
  {
    id: '2', owner_id: 'owner1', name: 'Beta', slug: 'beta', 
    status: ProjectStatus.PLANNING, priority: ProjectPriority.LOW, 
    tech_stack: [], created_at: '2023-01-01', updated_at: '2023-01-01'
  }
]


vi.mock('../lib/analyticsApi', () => ({
  analyticsApi: { getDashboard: vi.fn().mockResolvedValue({ 
    total_projects: 2, 
    active_projects: 1,
    completed_projects: 0,
    total_tasks: 0,
    completed_tasks: 0,
    in_progress_tasks: 0,
    overdue_tasks: 0
  }) }
}))

vi.mock('../lib/axios', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: [] })
  }
}))

describe('Projects & Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Dashboard with projects', async () => {
    (projectApi.list as any).mockResolvedValue({ items: mockProjects })
    
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    )

    expect(await screen.findByText(/Welcome back, Test User/i)).toBeInTheDocument()
    
    await waitFor(() => {
      expect(screen.getByText('Alpha')).toBeInTheDocument()
      expect(screen.getByText('Beta')).toBeInTheDocument()
    })
  })

  it('renders Dashboard empty state', async () => {
    (projectApi.list as any).mockResolvedValue({ items: [] })
    
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/No projects yet/i)).toBeInTheDocument()
    })
  })

  it('renders Projects page and project cards', async () => {
    (projectApi.list as any).mockResolvedValue({ items: mockProjects, total: 2, page: 1, page_size: 100, total_pages: 1 })
    
    render(
      <MemoryRouter>
        <Projects />
      </MemoryRouter>
    )

    expect(screen.getByText(/Manage your workspace projects/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Alpha')).toBeInTheDocument()
      expect(screen.getByText('React')).toBeInTheDocument()
    })
  })
})
