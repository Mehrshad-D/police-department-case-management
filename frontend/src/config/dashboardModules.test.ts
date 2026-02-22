import { describe, it, expect } from 'vitest'
import { getModulesForRoles } from './dashboardModules'

describe('dashboardModules', () => {
  it('returns modules for Detective role', () => {
    const modules = getModulesForRoles(['Detective'])
    expect(modules.length).toBeGreaterThan(0)
    expect(modules.some((m) => m.id === 'board')).toBe(true)
  })

  it('returns admin module only for System Administrator', () => {
    const adminModules = getModulesForRoles(['System Administrator']).filter((m) => m.id === 'admin')
    expect(adminModules.length).toBe(1)
    const detectiveModules = getModulesForRoles(['Detective']).filter((m) => m.id === 'admin')
    expect(detectiveModules.length).toBe(0)
  })

  it('is case insensitive', () => {
    const m1 = getModulesForRoles(['detective'])
    const m2 = getModulesForRoles(['Detective'])
    expect(m1.map((x) => x.id).sort()).toEqual(m2.map((x) => x.id).sort())
  })
})
