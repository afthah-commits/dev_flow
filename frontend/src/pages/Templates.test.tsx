/// <reference types="@testing-library/jest-dom" />
import React from "react";
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Templates from './Templates'
import ProjectForm from './ProjectForm'
import { projectTemplateApi } from '../lib/projectTemplateApi'
import { projectApi } from '../lib/projectApi'
import { ProjectTemplate } from '../types/template'

vi.mock('../lib/projectTemplateApi', () => ({
  projectTemplateApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    archive: vi.fn(),
    delete: vi.fn(),
    createProject: vi.fn(),
  }
}))

vi.mock('../lib/projectApi', () => ({
  projectApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  }
}))

vi.mock('../lib/analyticsApi', () => ({
  analyticsApi: { getDashboard: vi.fn().mockResolvedValue({
    total_projects: 0, active_projects: 0, completed_projects: 0,
    total_tasks: 0, completed_tasks: 0, in_progress_tasks: 0, overdue_tasks: 0,
  }) }
}))

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { name: 'Test User' }, isAuthenticated: true, isLoading: false, logout: vi.fn() }),
  AuthProvider: ({ children }: any) => <div>{children}</div>
}))

const template = (overrides: Partial<ProjectTemplate> = {}): ProjectTemplate => ({
  id: 'tpl-1',
  organization_id: 'org-1',
  name: 'Web Kickoff',
  description: 'Standard web app setup',
  is_archived: false,
  created_at: '2026-10-06T00:00:00Z',
  updated_at: '2026-10-06T00:00:00Z',
  tasks: [
    { id: 't1', template_id: 'tpl-1', title: 'Setup repo', description: undefined, priority: 'MEDIUM', position: 0, label_names: ['infra'], checklist_items: ['Create repo', 'Add CI'] },
    { id: 't2', template_id: 'tpl-1', title: 'Design schema', description: undefined, priority: 'HIGH', position: 1, label_names: [], checklist_items: [] },
  ],
  ...overrides,
})

describe('Templates page (Phase 44)', () => {
  beforeEach(() => { vi.clearAllMocks() })

  const renderPage = () => render(<MemoryRouter><Templates /></MemoryRouter>)

  it('renders the template list (template list)', async () => {
    (projectTemplateApi.list as any).mockResolvedValue([template()])
    renderPage()
    expect(await screen.findByText('Web Kickoff')).toBeInTheDocument()
    expect(screen.getByTestId('template-task-count-tpl-1').textContent).toContain('2 template tasks')
  })

  it('shows a loading state first (loading state)', async () => {
    (projectTemplateApi.list as any).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByTestId('templates-loading')).toBeInTheDocument()
  })

  it('shows an empty state when no templates exist (empty state)', async () => {
    (projectTemplateApi.list as any).mockResolvedValue([])
    renderPage()
    expect(await screen.findByTestId('templates-empty')).toBeInTheDocument()
  })

  it('shows an error state when loading fails (error state)', async () => {
    (projectTemplateApi.list as any).mockRejectedValue(new Error('boom'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to load templates')
  })

  it('creates a template with tasks (create template)', async () => {
    (projectTemplateApi.list as any).mockResolvedValue([]);
    (projectTemplateApi.create as any).mockResolvedValue(template())
    renderPage()

    fireEvent.click(await screen.findByText('New Template'))
    fireEvent.change(screen.getByPlaceholderText('e.g. Standard Web App Kickoff'), { target: { value: 'My Template' } })
    fireEvent.change(screen.getByPlaceholderText('Task 1 title'), { target: { value: 'First task' } })
    fireEvent.click(screen.getByText('Create Template'))

    await waitFor(() => {
      expect(projectTemplateApi.create).toHaveBeenCalledWith(expect.objectContaining({
        name: 'My Template',
        tasks: [expect.objectContaining({ title: 'First task' })],
      }))
    })
  })

  it('edits a template (edit template)', async () => {
    (projectTemplateApi.list as any).mockResolvedValue([template()]);
    (projectTemplateApi.update as any).mockResolvedValue(template())
    renderPage()

    fireEvent.click(await screen.findByText('Edit'))
    const nameInput = screen.getByPlaceholderText('e.g. Standard Web App Kickoff')
    expect((nameInput as HTMLInputElement).value).toBe('Web Kickoff')
    fireEvent.change(nameInput, { target: { value: 'Renamed' } })
    fireEvent.click(screen.getByText('Save Changes'))

    await waitFor(() => {
      expect(projectTemplateApi.update).toHaveBeenCalledWith('tpl-1', expect.objectContaining({ name: 'Renamed' }))
    })
  })

  it('archives a template (archive)', async () => {
    (projectTemplateApi.list as any).mockResolvedValue([template()]);
    (projectTemplateApi.archive as any).mockResolvedValue(template({ is_archived: true }))
    renderPage()

    fireEvent.click(await screen.findByText('Archive'))
    await waitFor(() => expect(projectTemplateApi.archive).toHaveBeenCalledWith('tpl-1'))
  })

  it('deletes a template after confirmation (delete)', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    (projectTemplateApi.list as any).mockResolvedValue([template()]);
    (projectTemplateApi.delete as any).mockResolvedValue(undefined)
    renderPage()

    fireEvent.click(await screen.findByText('Delete'))
    await waitFor(() => expect(projectTemplateApi.delete).toHaveBeenCalledWith('tpl-1'))
  })

  it('previews template tasks and creates a project from it (preview + create project from template)', async () => {
    (projectTemplateApi.list as any).mockResolvedValue([template()]);
    (projectTemplateApi.createProject as any).mockResolvedValue({ project_id: 'p9', name: 'New App', slug: 'new-app', tasks_created: 2 })
    renderPage()

    // preview shows task titles
    expect(await screen.findByText('Setup repo')).toBeInTheDocument()
    expect(screen.getByText('Design schema')).toBeInTheDocument()
    expect(screen.getByText('(2 checklist items)')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Create Project'))
    expect(screen.getByTestId('apply-template-name').textContent).toContain('Web Kickoff')
    fireEvent.change(screen.getByPlaceholderText('e.g. Customer Portal v2'), { target: { value: 'New App' } })
    fireEvent.click(screen.getByTestId('apply-template-submit'))

    await waitFor(() => {
      expect(projectTemplateApi.createProject).toHaveBeenCalledWith('tpl-1', { name: 'New App', description: undefined })
    })
  })
})

describe('ProjectForm with templates (Phase 44)', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('keeps blank project creation working (blank project creation)', async () => {
    (projectTemplateApi.list as any).mockResolvedValue([template()]);
    (projectApi.create as any).mockResolvedValue({ id: 'p1', name: 'Blank' })
    render(
      <MemoryRouter initialEntries={["/projects/new"]}>
        <Routes>
          <Route path="/projects/new" element={<ProjectForm />} />
          <Route path="/projects/:projectId" element={<div>details</div>} />
        </Routes>
      </MemoryRouter>
    )
    fireEvent.click(await screen.findByTestId('mode-blank'))
    fireEvent.change(screen.getByLabelText('Project Name *'), { target: { value: 'Blank' } })
    fireEvent.click(screen.getByTestId('project-submit'))
    await waitFor(() => expect(projectApi.create).toHaveBeenCalled())
    expect(projectTemplateApi.createProject).not.toHaveBeenCalled()
  })

  it('creates a project from a selected template (create project from template)', async () => {
    (projectTemplateApi.list as any).mockResolvedValue([template()]);
    (projectTemplateApi.createProject as any).mockResolvedValue({ project_id: 'p2', name: 'From Tpl', slug: 'from-tpl', tasks_created: 2 })
    render(
      <MemoryRouter initialEntries={["/projects/new"]}>
        <Routes>
          <Route path="/projects/new" element={<ProjectForm />} />
          <Route path="/projects/:projectId" element={<div>details</div>} />
        </Routes>
      </MemoryRouter>
    )
    fireEvent.click(await screen.findByTestId('mode-template'))
    fireEvent.change(screen.getByTestId('template-select'), { target: { value: 'tpl-1' } })
    expect(screen.getByTestId('template-hint').textContent).toContain('2 template task')
    fireEvent.change(screen.getByLabelText('Project Name *'), { target: { value: 'From Tpl' } })
    fireEvent.click(screen.getByTestId('project-submit'))
    await waitFor(() => {
      expect(projectTemplateApi.createProject).toHaveBeenCalledWith('tpl-1', { name: 'From Tpl', description: '' })
    })
    expect(projectApi.create).not.toHaveBeenCalled()
  })
})
