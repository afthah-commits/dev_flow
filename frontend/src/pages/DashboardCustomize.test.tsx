/// <reference types="@testing-library/jest-dom" />
import React from "react";
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from './Dashboard'
import { dashboardApi } from '../lib/dashboardApi'
import { projectApi } from '../lib/projectApi'
import { analyticsApi } from '../lib/analyticsApi'
import { DashboardWidgetPlacement } from '../types/dashboard'

vi.mock('../lib/dashboardApi', () => ({
  dashboardApi: {
    getLayout: vi.fn(),
    saveLayout: vi.fn(),
    resetLayout: vi.fn(),
  }
}))

vi.mock('../lib/projectApi', () => ({
  projectApi: {
    list: vi.fn(),
    delete: vi.fn(),
  }
}))

vi.mock('../lib/analyticsApi', () => ({
  analyticsApi: {
    getDashboard: vi.fn(),
  }
}))

import { api } from '../lib/axios'

vi.mock('../lib/axios', () => ({
  api: {
    get: vi.fn(),
  }
}))

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { name: 'Test User' }, isAuthenticated: true, isLoading: false, logout: vi.fn() }),
  AuthProvider: ({ children }: any) => <div>{children}</div>
}))

vi.mock('../lib/organizationApi', () => ({ organizationApi: {} }))

const defaults: DashboardWidgetPlacement[] = [
  { id: 'stats', visible: true },
  { id: 'active_sprints', visible: true },
  { id: 'recent_projects', visible: true },
]

beforeEach(() => {
  vi.clearAllMocks();
  (dashboardApi.getLayout as any).mockResolvedValue({
    widgets: defaults, defaults: ['stats', 'active_sprints', 'recent_projects'], customized: false,
  });
  (analyticsApi.getDashboard as any).mockResolvedValue({
    active_projects: 1, total_tasks: 5, completed_tasks: 2, overdue_tasks: 1,
  });
  (projectApi.list as any).mockResolvedValue({ items: [] });
  (api.get as any).mockResolvedValue({ data: [] });
})

const renderDash = () => render(<MemoryRouter><Dashboard /></MemoryRouter>)

describe('Dashboard customization (Phase 45)', () => {
  it('loads the dashboard with default widgets (dashboard loads)', async () => {
    renderDash()
    expect(await screen.findByTestId('widget-stats')).toBeInTheDocument()
    expect(screen.getByTestId('widget-active_sprints')).toBeInTheDocument()
    expect(screen.getByTestId('widget-recent_projects')).toBeInTheDocument()
    expect(dashboardApi.getLayout).toHaveBeenCalled()
  })

  it('enters customize mode via the Customize button (customize mode)', async () => {
    renderDash()
    fireEvent.click(await screen.findByTestId('customize-button'))
    expect(screen.getByTestId('customize-panel')).toBeInTheDocument()
    expect(screen.getByTestId('save-layout')).toBeInTheDocument()
    expect(screen.getByTestId('cancel-customize')).toBeInTheDocument()
    expect(screen.getByTestId('reset-layout')).toBeInTheDocument()
  })

  it('hides a widget and persists the choice on save (hide widget + save)', async () => {
    (dashboardApi.saveLayout as any).mockResolvedValue({
      widgets: [defaults[0], { ...defaults[1], visible: false }, defaults[2]],
      defaults: ['stats', 'active_sprints', 'recent_projects'],
      customized: true,
    })
    renderDash()
    fireEvent.click(await screen.findByTestId('customize-button'))
    fireEvent.click(screen.getByTestId('widget-toggle-active_sprints'))
    expect(screen.getByTestId('widget-toggle-active_sprints')).not.toBeChecked()
    fireEvent.click(screen.getByTestId('save-layout'))

    await waitFor(() => {
      expect(dashboardApi.saveLayout).toHaveBeenCalledWith([
        { id: 'stats', visible: true },
        { id: 'active_sprints', visible: false },
        { id: 'recent_projects', visible: true },
      ])
    })
  })

  it('shows a previously hidden widget (show widget)', async () => {
    (dashboardApi.getLayout as any).mockResolvedValue({
      widgets: [defaults[0], { ...defaults[1], visible: false }, defaults[2]],
      defaults: ['stats', 'active_sprints', 'recent_projects'],
      customized: true,
    })
    renderDash()
    fireEvent.click(await screen.findByTestId('customize-button'))
    const toggle = screen.getByTestId('widget-toggle-active_sprints')
    expect(toggle).not.toBeChecked()
    fireEvent.click(toggle)
    expect(toggle).toBeChecked()
  })

  it('reorders widgets with move up/down (reorder widget)', async () => {
    renderDash()
    fireEvent.click(await screen.findByTestId('customize-button'))
    fireEvent.click(screen.getByTestId('widget-down-stats'))
    fireEvent.click(screen.getByTestId('save-layout'))

    await waitFor(() => {
      expect(dashboardApi.saveLayout).toHaveBeenCalledWith([
        { id: 'active_sprints', visible: true },
        { id: 'stats', visible: true },
        { id: 'recent_projects', visible: true },
      ])
    })
  })

  it('cancels customization without saving (cancel)', async () => {
    renderDash()
    fireEvent.click(await screen.findByTestId('customize-button'))
    fireEvent.click(screen.getByTestId('widget-toggle-stats'))
    fireEvent.click(screen.getByTestId('cancel-customize'))
    expect(screen.queryByTestId('customize-panel')).not.toBeInTheDocument()
    expect(dashboardApi.saveLayout).not.toHaveBeenCalled()
  })

  it('restores default layout via reset (reset defaults)', async () => {
    // getLayout returns the stale customized layout until reset happens
    // (exactly like the real backend); after reset it returns the defaults.
    let resetDone = false;
    (dashboardApi.getLayout as any).mockImplementation(() => Promise.resolve(
      resetDone
        ? { widgets: defaults, defaults: ['stats', 'active_sprints', 'recent_projects'], customized: false }
        : { widgets: [{ id: 'recent_projects', visible: true }], defaults: ['stats', 'active_sprints', 'recent_projects'], customized: true }
    ));
    (dashboardApi.resetLayout as any).mockImplementation(() => {
      resetDone = true;
      return Promise.resolve({
        widgets: defaults, defaults: ['stats', 'active_sprints', 'recent_projects'], customized: false,
      });
    })
    renderDash()
    expect(await screen.findByTestId('widget-recent_projects')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('customize-button'))
    fireEvent.click(screen.getByTestId('reset-layout'))

    expect(await screen.findByTestId('widget-stats')).toBeInTheDocument()
    expect(screen.getByTestId('widget-active_sprints')).toBeInTheDocument()
    expect(dashboardApi.resetLayout).toHaveBeenCalled()
  })

  it('renders with defaults when the layout API fails (error resilience)', async () => {
    (dashboardApi.getLayout as any).mockRejectedValue(new Error('offline'))
    renderDash()
    // still functional with defaults
    expect(await screen.findByTestId('widget-stats')).toBeInTheDocument()
    expect(screen.getByTestId('widget-recent_projects')).toBeInTheDocument()
  })

  it('shows an error when saving fails (error state)', async () => {
    (dashboardApi.saveLayout as any).mockRejectedValue(new Error('boom'))
    renderDash()
    fireEvent.click(await screen.findByTestId('customize-button'))
    fireEvent.click(screen.getByTestId('save-layout'))
    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to save dashboard layout')
  })

  it('skips fetching widget data for hidden widgets (performance)', async () => {
    (dashboardApi.getLayout as any).mockResolvedValue({
      widgets: [{ id: 'recent_projects', visible: true }, { id: 'stats', visible: false }, { id: 'active_sprints', visible: false }],
      defaults: ['stats', 'active_sprints', 'recent_projects'],
      customized: true,
    })
    renderDash()
    await waitFor(() => expect(projectApi.list).toHaveBeenCalled())
    expect(analyticsApi.getDashboard).not.toHaveBeenCalled()
    expect(screen.queryByTestId('widget-stats')).not.toBeInTheDocument()
    expect(screen.queryByTestId('widget-active_sprints')).not.toBeInTheDocument()
  })
})
