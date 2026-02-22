import { useState } from 'react'
import { useEvidenceList } from '@/hooks/useEvidence'
import { useEvidenceCreate } from '@/hooks/useEvidence'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { CardSkeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'
import type { Evidence } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data as { results: T[] }).results ?? []
}

export function DocumentsPage() {
  const [caseId, setCaseId] = useState<string>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [type, setType] = useState<string>('other')

  const { data, isLoading, error } = useEvidenceList(caseId ? parseInt(caseId, 10) : null)
  const createEvidence = useEvidenceCreate()
  const list = data ? ensureArray(data as Evidence[] | { results: Evidence[] }) : []

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!caseId || !title) return
    const payload = new FormData()
    payload.append('case', caseId)
    payload.append('evidence_type', type)
    payload.append('title', title)
    payload.append('description', description)
    createEvidence.mutate(payload, { onSuccess: () => { setModalOpen(false); setTitle(''); setDescription(''); } })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-slate-100">Documents & Evidence</h1>
        <div className="flex gap-2">
          <Input
            type="number"
            placeholder="Case ID"
            value={caseId}
            onChange={(e) => setCaseId(e.target.value)}
            className="w-28"
          />
          <Button onClick={() => setModalOpen(true)}>Add evidence</Button>
        </div>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Add evidence">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Case ID</label>
            <Input type="number" value={caseId} onChange={(e) => setCaseId(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Type</label>
            <select
              className="w-full rounded-lg bg-slate-800 border border-slate-600 text-slate-100 px-4 py-2.5"
              value={type}
              onChange={(e) => setType(e.target.value)}
            >
              <option value="witness">Witness</option>
              <option value="biological">Biological</option>
              <option value="vehicle">Vehicle</option>
              <option value="id_document">ID Document</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Title</label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Description</label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          {createEvidence.isError && (
            <p className="text-sm text-red-400">{getApiErrorMessage(createEvidence.error)}</p>
          )}
          <Button type="submit" loading={createEvidence.isPending}>Save</Button>
        </form>
      </Modal>

      {error && <p className="text-red-400">Failed to load evidence.</p>}
      {!caseId && <Card><CardContent className="py-12 text-center text-slate-500">Enter a case ID to list evidence.</CardContent></Card>}
      {caseId && isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (<CardSkeleton key={i} />))}
        </div>
      )}
      {caseId && !isLoading && list.length === 0 && (
        <Card><CardContent className="py-12 text-center text-slate-500">No evidence for this case.</CardContent></Card>
      )}
      {caseId && !isLoading && list.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {list.map((e) => (
            <Card key={e.id}>
              <CardHeader>
                <CardTitle className="text-base truncate">{e.title}</CardTitle>
                <span className="text-xs text-slate-500">{e.evidence_type}</span>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-500 line-clamp-2">{e.description || '—'}</p>
                <p className="text-xs text-slate-600 mt-2">{formatDate(e.date_recorded)} · {e.recorder_username ?? '—'}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
