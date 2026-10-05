import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ProjectDetails from './ProjectDetails'
import { projectApi } from '../lib/projectApi'
import { taskApi } from '../lib/taskApi'
import { TaskStatus, TaskPriority } from '../types/task'

vi.mock('../lib/projectApi', () => ({
  projectApi: { get: vi.fn() }
}))
vi.mock('../lib/taskApi', () => ({
  taskApi: { getStats: vi.fn(), list: vi.fn(), create: vi.fn(), updateStatus: vi.fn(), delete: vi.fn() }
}))

const mockProject = { id: '1', name: 'Test Proj', status: 'Active', description: 'Desc' }
const mockStats = { total: 2, todo: 1, in_progress: 1, in_review: 0, done: 0, overdue: 0 }
const mockTasks = [
  { id: 't1', title: 'Task 1', status: TaskStatus.TODO, priority: TaskPriority.HIGH, labels: [] },
  { id: 't2', title: 'Task 2', status: TaskStatus.IN_PROGRESS, priority: TaskPriority.LOW, labels: ['Bug'] }
]

describe('ProjectDetails & Tasks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (projectApi.get as any).mockResolvedValue(mockProject);
    (taskApi.getStats as any).mockResolvedValue(mockStats);
    (taskApi.list as any).mockResolvedValue({ items: mockTasks });
  })

  it('renders Kanban board with tasks', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/1']}>
        <Routes>
          <Route path="/projects/:projectId" element={<ProjectDetails />} />
        </Routes>
      </MemoryRouter>
    )

    expect(await screen.findByText('Test Proj')).toBeInTheDocument()
    // The kanban lives under the Tasks tab (Overview is the default tab).
    fireEvent.click(screen.getByText('Tasks'))
    expect(await screen.findByText('Task 1')).toBeInTheDocument()
    expect(await screen.findByText('Task 2')).toBeInTheDocument()
    expect(await screen.findByText('Bug')).toBeInTheDocument()
  })

  it('switches to list view', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/1']}>
        <Routes>
          <Route path="/projects/:projectId" element={<ProjectDetails />} />
        </Routes>
      </MemoryRouter>
    )
    
    await screen.findByText('Test Proj')

    // Open the Tasks tab where the view switcher lives.
    fireEvent.click(screen.getByText('Tasks'))
    const listBtn = await screen.findByText('List View')
    fireEvent.click(listBtn)
    
    expect(await screen.findByText('Title')).toBeInTheDocument()
    expect(await screen.findByText('Task 1')).toBeInTheDocument()
  })

  it('opens task form', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/1']}>
        <Routes>
          <Route path="/projects/:projectId" element={<ProjectDetails />} />
        </Routes>
      </MemoryRouter>
    )
    
    await screen.findByText('Test Proj')
    const addBtn = screen.getByText('Add Task')
    fireEvent.click(addBtn)
    
    expect(screen.getByText('New Task')).toBeInTheDocument()
    expect(screen.getByText('Title *')).toBeInTheDocument()
  })
})
