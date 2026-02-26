vi.mock('@/api/client', () => ({
  getApiErrorMessage: () => 'Mocked error',
}))

import { screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { LoginPage } from './LoginPage'
import { renderWithProviders } from '@/test/renderWithProviders'
import { authApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/authStore'

// ------------------
// Mocks
// ------------------
vi.mock('@/api/endpoints', () => ({
  authApi: {
    login: vi.fn(),
  },
}))
const mockNavigate = vi.fn()

vi.mock('react-router-dom', async (orig) => {
  const actual = await orig()
  return {
    ...(actual as object),
    useNavigate: () => mockNavigate,
  }
})
vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

// ------------------

describe('LoginPage', () => {
  const mockSetAuth = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    ;(useAuthStore as any).mockImplementation((selector: any) =>
      selector({ setAuth: mockSetAuth })
    )
  })

  it('renders login form', () => {
    renderWithProviders(<LoginPage />)

    expect(
    screen.getByRole('heading', { name: /sign in/i })
    ).toBeInTheDocument()

    expect(
    screen.getByRole('button', { name: /sign in/i })
    ).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Identifier')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
  })

  it('does not submit if fields are empty', async () => {
    renderWithProviders(<LoginPage />)

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(authApi.login).not.toHaveBeenCalled()
    })
  })

  it('submits form and redirects on success', async () => {
    ;(authApi.login as any).mockResolvedValue({
      user: { id: 1, username: 'sana' },
      tokens: { access: 'access-token', refresh: 'refresh-token' },
    })

    renderWithProviders(<LoginPage />)

    fireEvent.change(screen.getByPlaceholderText('Identifier'), {
      target: { value: 'sana' },
    })

    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'password123' },
    })

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith('sana', 'password123')
    })

    expect(mockSetAuth).toHaveBeenCalledWith(
      { id: 1, username: 'sana' },
      'access-token',
      'refresh-token'
    )

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('shows error message on failure', async () => {
    ;(authApi.login as any).mockRejectedValue(new Error('Invalid credentials'))

    renderWithProviders(<LoginPage />)

    fireEvent.change(screen.getByPlaceholderText('Identifier'), {
      target: { value: 'wrong' },
    })

    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'wrongpass' },
    })

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/mocked error/i)).toBeInTheDocument()
    })
  })
})