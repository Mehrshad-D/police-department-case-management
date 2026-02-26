vi.mock('@/api/client', () => ({
  getApiErrorMessage: () => 'Mocked error',
}))

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithProviders } from '@/test/renderWithProviders'

// mock BEFORE import
vi.mock('@/api/endpoints', () => ({
  authApi: {
    register: vi.fn(),
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

import { RegisterPage } from './RegisterPage'
import { authApi } from '@/api/endpoints'

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form fields', () => {
    renderWithProviders(<RegisterPage />)

    expect(screen.getByText(/create account/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('National ID')).toBeInTheDocument()
  })

  it('does not submit if form incomplete', async () => {
    renderWithProviders(<RegisterPage />)

    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() => {
      expect(authApi.register).not.toHaveBeenCalled()
    })
  })

  it('submits successfully', async () => {
    (authApi.register as any).mockResolvedValue({})

    renderWithProviders(<RegisterPage />)

    const fill = (placeholder: string, value: string) =>
      fireEvent.change(screen.getByPlaceholderText(placeholder), {
        target: { value },
      })

    fill('Username', 'sana')
    fill('••••••••', 'password123')
    fill('Email', 'sana@test.com')
    fill('Phone', '123456')
    fill('Full name', 'Sana Test')
    fill('National ID', 'ABC123')

    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalled()
    })

    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  it('shows error on failure', async () => {
    (authApi.register as any).mockRejectedValue(new Error('error'))

    renderWithProviders(<RegisterPage />)

    fireEvent.change(screen.getByPlaceholderText('Username'), {
      target: { value: 'sana' },
    })

    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'password123' },
    })

    fireEvent.change(screen.getByPlaceholderText('Email'), {
      target: { value: 'sana@test.com' },
    })

    fireEvent.change(screen.getByPlaceholderText('Phone'), {
      target: { value: '1234567890' },
    })

    fireEvent.change(screen.getByPlaceholderText('Full name'), {
      target: { value: 'Sana Babayan' },
    })

    fireEvent.change(screen.getByPlaceholderText('National ID'), {
      target: { value: '0011223344' },
    })

    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() => {
      expect(screen.getByText(/mocked error/i)).toBeInTheDocument()
    })
  })

  it('renders login link', () => {
    renderWithProviders(<RegisterPage />)

    expect(screen.getByText(/sign in/i)).toBeInTheDocument()
  })
})