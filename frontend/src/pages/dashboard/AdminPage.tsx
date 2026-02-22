import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi, rolesApi } from '@/api/endpoints'
import { useStatistics } from '@/hooks/useStatistics'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatNumber } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'
import type { User } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data as { results: T[] }).results ?? []
}

export function AdminPage() {
  const [userModalOpen, setUserModalOpen] = useState(false)
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [roleIds, setRoleIds] = useState<number[]>([])
  const qc = useQueryClient()

  const { data: stats } = useStatistics()
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list(),
  })
  const { data: rolesData, isLoading: rolesLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => rolesApi.list(),
  })
  const roles = ensureArray(rolesData ?? [])
  const usersList = usersData ? ensureArray(usersData as User[] | { results: User[] }) : []

  const updateUser = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { role_ids: number[] } }) => usersApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      setUserModalOpen(false)
      setSelectedUserId(null)
    },
  })

  const openUserRoles = (u: User) => {
    setSelectedUserId(u.id)
    setRoleIds(u.roles?.map((r) => r.id) ?? [])
    setUserModalOpen(true)
  }

  const toggleRole = (roleId: number) => {
    setRoleIds((prev) => (prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId]))
  }

  const handleSaveRoles = () => {
    if (selectedUserId == null) return
    updateUser.mutate({ id: selectedUserId, data: { role_ids: roleIds } })
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-100">Admin Panel</h1>

      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader><CardTitle className="text-slate-400 text-sm">Users</CardTitle></CardHeader>
            <CardContent><p className="text-2xl font-bold text-primary-400">{formatNumber(stats.users_total)}</p></CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-slate-400 text-sm">Cases</CardTitle></CardHeader>
            <CardContent><p className="text-2xl font-bold text-primary-400">{formatNumber(stats.cases_total)}</p></CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-slate-400 text-sm">Complaints</CardTitle></CardHeader>
            <CardContent><p className="text-2xl font-bold text-primary-400">{formatNumber(stats.complaints_total)}</p></CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-slate-400 text-sm">Evidence</CardTitle></CardHeader>
            <CardContent><p className="text-2xl font-bold text-primary-400">{formatNumber(stats.evidence_total)}</p></CardContent>
          </Card>
        </div>
      )}

      <section>
        <h2 className="text-lg font-semibold text-slate-100 mb-4">User management</h2>
        {usersLoading && <Skeleton className="h-64 w-full" />}
        {!usersLoading && (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left p-4 text-slate-400 font-medium">Username</th>
                      <th className="text-left p-4 text-slate-400 font-medium">Full name</th>
                      <th className="text-left p-4 text-slate-400 font-medium">Roles</th>
                      <th className="text-left p-4 text-slate-400 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usersList.map((u) => (
                      <tr key={u.id} className="border-b border-slate-700/50 hover:bg-slate-800/30">
                        <td className="p-4 text-slate-200">{u.username}</td>
                        <td className="p-4 text-slate-400">{u.full_name || '—'}</td>
                        <td className="p-4 text-slate-400">{(u.role_names ?? []).join(', ') || '—'}</td>
                        <td className="p-4">
                          <Button variant="ghost" size="sm" onClick={() => openUserRoles(u)}>
                            Assign roles
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </section>

      <Modal open={userModalOpen} onClose={() => { setUserModalOpen(false); setSelectedUserId(null); }} title="Assign roles">
        <div className="space-y-4">
          {rolesLoading && <p className="text-slate-400 text-sm">Loading roles…</p>}
          {!rolesLoading && roles.length === 0 && <p className="text-slate-400 text-sm">No roles available. Run <code className="bg-slate-800 px-1 rounded">python manage.py seed_roles</code> in the backend.</p>}
          {!rolesLoading && roles.map((r) => (
            <label key={r.id} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={roleIds.includes(r.id)}
                onChange={() => toggleRole(r.id)}
                className="rounded border-slate-600 bg-slate-800 text-primary-500"
              />
              <span className="text-slate-200">{r.name}</span>
            </label>
          ))}
          {updateUser.isError && <p className="text-sm text-red-400">{getApiErrorMessage(updateUser.error)}</p>}
          <Button onClick={handleSaveRoles} loading={updateUser.isPending}>Save</Button>
        </div>
      </Modal>
    </div>
  )
}
