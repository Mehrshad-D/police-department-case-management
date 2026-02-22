import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from './authStore'

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.getState().logout()
  })

  it('starts with null user', () => {
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('setAuth stores user and tokens', () => {
    const user = { id: 1, username: 'test', role_names: ['Detective'] } as any
    useAuthStore.getState().setAuth(user, 'access', 'refresh')
    expect(useAuthStore.getState().user?.username).toBe('test')
  })

  it('hasRole returns true when user has role', () => {
    const user = { id: 1, username: 'test', role_names: ['Detective'] } as any
    useAuthStore.getState().setAuth(user, 'a', 'r')
    expect(useAuthStore.getState().hasRole('Detective')).toBe(true)
    expect(useAuthStore.getState().hasRole('Admin')).toBe(false)
  })

  it('logout clears state', () => {
    const user = { id: 1, username: 'test', role_names: [] } as any
    useAuthStore.getState().setAuth(user, 'a', 'r')
    useAuthStore.getState().logout()
    expect(useAuthStore.getState().user).toBeNull()
  })
})
