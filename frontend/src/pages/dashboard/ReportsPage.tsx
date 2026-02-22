import { useParams } from 'react-router-dom'
import { useCase } from '@/hooks/useCases'
import { useEvidenceList } from '@/hooks/useEvidence'
import { useSuspectsList } from '@/hooks/useSuspects'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data as { results: T[] }).results ?? []
}

export function ReportsPage() {
  const { id } = useParams<{ id?: string }>()
  const caseId = id ? parseInt(id, 10) : null
  const { data: caseData, isLoading } = useCase(caseId)
  const { data: evidenceData } = useEvidenceList(caseId)
  const { data: suspectsData } = useSuspectsList(caseId ? { case: caseId } : undefined)
  const evidenceList = evidenceData ? ensureArray(evidenceData) : []
  const suspectsList = suspectsData ? ensureArray(suspectsData) : []

  const handlePrint = () => window.print()

  if (!caseId) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-100">Case Report</h1>
        <Card><CardContent className="py-12 text-center text-slate-500">Select a case from the Cases module to view its report.</CardContent></Card>
      </div>
    )
  }

  if (isLoading || !caseData) {
    return <Skeleton className="h-96 w-full" />
  }

  return (
    <div className="space-y-6 print:space-y-4">
      <div className="flex justify-between items-center print:hidden">
        <h1 className="text-2xl font-bold text-slate-100">Case Report</h1>
        <Button variant="primary" onClick={handlePrint}>Print report</Button>
      </div>

      <div className="bg-slate-900 rounded-xl border border-slate-700 p-6 print:border print:shadow-none">
        <h2 className="text-xl font-semibold text-slate-100 mb-4">{caseData.title}</h2>
        <p className="text-slate-400 mb-6">{caseData.description || '—'}</p>

        <section className="mb-6">
          <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-2">Case details</h3>
          <dl className="grid gap-2 text-sm">
            <div><dt className="text-slate-500">Status</dt><dd className="text-slate-200">{caseData.status.replace(/_/g, ' ')}</dd></div>
            <div><dt className="text-slate-500">Created by</dt><dd className="text-slate-200">{caseData.created_by_username}</dd></div>
            <div><dt className="text-slate-500">Assigned detective</dt><dd className="text-slate-200">{caseData.assigned_detective_username ?? '—'}</dd></div>
            <div><dt className="text-slate-500">Created</dt><dd className="text-slate-200">{formatDate(caseData.created_at)}</dd></div>
          </dl>
        </section>

        <section className="mb-6">
          <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-2">Evidence ({evidenceList.length})</h3>
          <ul className="space-y-2">
            {evidenceList.map((e) => (
              <li key={e.id} className="text-sm text-slate-300">
                [{e.evidence_type}] {e.title} — {formatDate(e.date_recorded)}
              </li>
            ))}
            {evidenceList.length === 0 && <li className="text-slate-500">No evidence recorded.</li>}
          </ul>
        </section>

        <section>
          <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-2">Suspects ({suspectsList.length})</h3>
          <ul className="space-y-2">
            {suspectsList.map((s) => (
              <li key={s.id} className="text-sm text-slate-300">
                {s.user_username} — {s.status.replace(/_/g, ' ')}
              </li>
            ))}
            {suspectsList.length === 0 && <li className="text-slate-500">No suspects.</li>}
          </ul>
        </section>
      </div>
    </div>
  )
}
