import { useParams, useNavigate } from 'react-router-dom'
import { useCase } from '@/hooks/useCases'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'

const SEVERITY_MAP: Record<number, string> = {
  3: 'Level 3 - Minor',
  2: 'Level 2 - Moderate',
  1: 'Level 1 - Major',
  0: 'Crisis',
}

export function CaseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const caseId = id ? parseInt(id, 10) : null
  const { data: caseData, isLoading, error } = useCase(caseId)

  if (error || (caseId && !isLoading && !caseData)) {
    return (
      <div>
        <p className="text-red-400">Case not found.</p>
        <Button variant="ghost" onClick={() => navigate('/dashboard/cases')}>Back to list</Button>
      </div>
    )
  }

  if (isLoading || !caseData) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard/cases')}>
          ← Back
        </Button>
        <Button variant="secondary" size="sm" onClick={() => navigate(`/dashboard/reports/${caseData.id}`)}>
          View report
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>{caseData.title}</CardTitle>
          <div className="flex flex-wrap gap-2 mt-2">
            <span className="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-300">
              {caseData.status.replace(/_/g, ' ')}
            </span>
            <span className="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-300">
              {SEVERITY_MAP[caseData.severity] ?? caseData.severity}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-slate-300">{caseData.description || '—'}</p>
          <dl className="grid gap-2 text-sm">
            <div><dt className="text-slate-500">Created by</dt><dd>{caseData.created_by_username ?? '—'}</dd></div>
            <div><dt className="text-slate-500">Assigned detective</dt><dd>{caseData.assigned_detective_username ?? '—'}</dd></div>
            <div><dt className="text-slate-500">Created</dt><dd>{formatDate(caseData.created_at)}</dd></div>
          </dl>
        </CardContent>
      </Card>
    </div>
  )
}
