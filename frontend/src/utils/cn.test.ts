import { describe, it, expect } from 'vitest'
import { cn } from './cn'

describe('cn', () => {
  it('joins class names', () => {
    expect(cn('a', 'b')).toBe('a b')
  })

  it('filters falsy values', () => {
    expect(cn('a', undefined, 'b', null, false, 'c')).toBe('a b c')
  })

  it('supports conditional object', () => {
    expect(cn('base', { active: true, disabled: false })).toBe('base active')
  })
})
