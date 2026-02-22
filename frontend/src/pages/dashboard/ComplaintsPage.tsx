import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useComplaintsList, useComplaintCreate } from '@/hooks/useComplaints'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { CardSkeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'
import type { Complaint } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : data.results ?? []
}

const statusColor: Record<string, string> = {
  draft: 'bg-slate-600/20 text-slate-400',
  pending_trainee: 'bg-amber-500/20 text-amber-400',
  correction_needed: 'bg-orange-500/20 text-orange-400',
  pending_officer: 'bg-blue-500/20 text-blue-400',
  approved: 'bg-green-500/20 text-green-400',
  rejected: 'bg-red-500/20 text-red-400',
}

export function ComplaintsPage() {
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const { data, isLoading, error } = useComplaintsList()
  const createComplaint = useComplaintCreate()
  const list = data ? ensureArray(data as Complaint[] | { results: Complaint[] }) : []
  const filtered = list.filter(
    (c) =>
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.complainant_username?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-slate-100">Complaints</h1>
        <div className="flex gap-2">
          <Input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs" />
          <Button onClick={() => setModalOpen(true)}>New complaint</Button>
        </div>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Submit complaint">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (!newTitle.trim() || !newDescription.trim()) return
            createComplaint.mutate(
              { title: newTitle.trim(), description: newDescription.trim() },
              {
                onSuccess: () => {
                  setModalOpen(false)
                  setNewTitle('')
                  setNewDescription('')
                },
              }
            )
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm text-slate-400 mb-1">Title</label>
            <Input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Description</label>
            <textarea
              className="w-full rounded-lg bg-slate-800 border border-slate-600 text-slate-100 px-4 py-2.5 min-h-[100px]"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              required
            />
          </div>
          {createComplaint.isError && <p className="text-sm text-red-400">{getApiErrorMessage(createComplaint.error)}</p>}
          <Button type="submit" loading={createComplaint.isPending}>Submit</Button>
        </form>
      </Modal>
      {error && <p className="text-red-400">Failed to load complaints.</p>}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (<CardSkeleton key={i} />))}
        </div>
      )}
      {!isLoading && filtered.length === 0 && (
        <Card><CardContent className="py-12 text-center text-slate-500">No complaints found.</CardContent></Card>
      )}
      {!isLoading && filtered.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((c) => (
            <Link key={c.id} to={`/dashboard/complaints/${c.id}`}>
              <Card hover className="h-full">
                <CardHeader className="flex flex-row items-start justify-between gap-2">
                  <CardTitle className="text-base truncate">{c.title}</CardTitle>
                  <span className={`shrink-0 rounded px-2 py-0.5 text-xs ${statusColor[c.status] ?? 'bg-slate-600/20'}`}>
                    {c.status.replace(/_/g, ' ')}
                  </span>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-500">By {c.complainant_username}</p>
                  <p className="text-xs text-slate-600 mt-2">{formatDate(c.created_at)}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
