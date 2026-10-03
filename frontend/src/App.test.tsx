/// <reference types="@testing-library/jest-dom" />
import React from "react";
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'

import Login from './pages/Login'
import Register from './pages/Register'

// Mocking useAuth for some tests could be done, but we'll do integration-style testing
// Let's test the rendering of Login and Register pages.


vi.mock('../lib/taskApi', () => ({
  taskApi: { getGlobalStats: vi.fn().mockResolvedValue({ total: 0, done: 0, overdue: 0 }) }
}))

describe('Authentication Flow', () => {
  it('renders login page correctly', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )
    expect(screen.getByText(/Sign in to your account/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument()
  })

  it('renders register page correctly', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </MemoryRouter>
    )
    expect(screen.getByText(/Create an account/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign up/i })).toBeInTheDocument()
  })
})
