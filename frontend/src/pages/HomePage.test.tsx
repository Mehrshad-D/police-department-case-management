import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '@/test/renderWithProviders'
import { HomePage } from './HomePage'

// ✅ mock statistics hook BEFORE component import
vi.mock('@/hooks/useStatistics', () => ({
  useStatistics: vi.fn(),
}))

import { useStatistics } from '@/hooks/useStatistics'

describe('HomePage', () => {
  it('renders hero section', () => {
    ;(useStatistics as any).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    })

    renderWithProviders(<HomePage />)

    expect(
      screen.getByText(/Case Management System/i)
    ).toBeInTheDocument()
  })

  it('shows loading skeletons', () => {
    (useStatistics as any).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    })

    renderWithProviders(<HomePage />)

    expect(screen.getAllByText((_, el) => el?.className.includes('animate') ?? false)).toBeTruthy()
  })

  it('shows error message', () => {
    ;(useStatistics as any).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('fail'),
    })

    renderWithProviders(<HomePage />)

    expect(
      screen.getByText(/failed to load statistics/i)
    ).toBeInTheDocument()
  })

  it('renders statistics when loaded', () => {
    ;(useStatistics as any).mockReturnValue({
      data: {
        cases_total: 10,
        cases_open: 5,
        complaints_total: 20,
        complaints_pending: 3,
        evidence_total: 50,
        suspects_high_priority: 2,
        suspects_total: 8,
      },
      isLoading: false,
      error: null,
    })

    renderWithProviders(<HomePage />)

    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('20')).toBeInTheDocument()
  })
})