import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useCase, useCaseUpdate } from '@/hooks/useCases'
import { usersApi } from '@/api/endpoints'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'

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
  const [selectedDetectiveId, setSelectedDetectiveId] = useState<number | ''>('')
  const [selectedSeverity, setSelectedSeverity] = useState<number>(3)

  const { data: detectivesData } = useQuery({
    queryKey: ['detectives'],
    queryFn: () => usersApi.listDetectives(),
  })
  const detectives = Array.isArray(detectivesData) ? detectivesData : []
  const updateCase = useCaseUpdate(caseId ?? 0)

  useEffect(() => {
    if (caseData?.assigned_detective != null) setSelectedDetectiveId(caseData.assigned_detective)
    else setSelectedDetectiveId('')
  }, [caseData?.assigned_detective])
  useEffect(() => {
    if (caseData?.severity != null) setSelectedSeverity(caseData.severity)
  }, [caseData?.severity])

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

          <div className="mt-4 pt-4 border-t border-slate-700">
            <label className="block text-sm font-medium text-slate-400 mb-2">Crime level (severity)</label>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(Number(e.target.value))}
                className="rounded-md border border-slate-600 bg-slate-800 text-slate-200 px-3 py-2 text-sm min-w-[180px]"
              >
                <option value={3}>{SEVERITY_MAP[3]}</option>
                <option value={2}>{SEVERITY_MAP[2]}</option>
                <option value={1}>{SEVERITY_MAP[1]}</option>
                <option value={0}>{SEVERITY_MAP[0]}</option>
              </select>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => updateCase.mutate({ severity: selectedSeverity })}
                loading={updateCase.isPending}
                disabled={caseId == null || selectedSeverity === caseData.severity}
              >
                Update severity
              </Button>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-700">
            <label className="block text-sm font-medium text-slate-400 mb-2">Assign detective</label>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={selectedDetectiveId === '' ? '' : selectedDetectiveId}
                onChange={(e) => setSelectedDetectiveId(e.target.value === '' ? '' : Number(e.target.value))}
                className="rounded-md border border-slate-600 bg-slate-800 text-slate-200 px-3 py-2 text-sm min-w-[180px]"
              >
                <option value="">— Unassigned —</option>
                {detectives.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.full_name || d.username}
                  </option>
                ))}
              </select>
              <Button
                size="sm"
                onClick={() => {
                  const value = selectedDetectiveId === '' ? null : selectedDetectiveId
                  updateCase.mutate({ assigned_detective: value })
                }}
                loading={updateCase.isPending}
                disabled={caseId == null}
              >
                {caseData.assigned_detective != null && selectedDetectiveId === caseData.assigned_detective ? 'Update' : 'Assign'}
              </Button>
            </div>
            {updateCase.isError && (
              <p className="text-sm text-red-400 mt-2">{getApiErrorMessage(updateCase.error)}</p>
            )}
            {detectives.length === 0 && (
              <p className="text-slate-500 text-xs mt-1">No detectives found. Assign the Detective role to users in Admin Panel.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
