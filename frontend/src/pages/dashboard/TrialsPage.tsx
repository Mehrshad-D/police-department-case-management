import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { trialsApi, verdictsApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/authStore'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'
import type { Trial, TrialFullDetail } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data as { results: T[] }).results ?? []
}

export function TrialsPage() {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const trialId = id ? parseInt(id, 10) : null

  const [verdictType, setVerdictType] = useState<'guilty' | 'innocent'>('guilty')
  const [punishmentTitle, setPunishmentTitle] = useState('')
  const [punishmentDescription, setPunishmentDescription] = useState('')
  const [verdictTitle, setVerdictTitle] = useState('')
  const [verdictDescription, setVerdictDescription] = useState('')

  const isJudge = user?.role_names?.some((r) => r.toLowerCase() === 'judge')
  const { data: trialsData, error: trialsError, isLoading: trialsLoading } = useQuery({
    queryKey: ['trials'],
    queryFn: () => trialsApi.list(),
    enabled: !!isJudge,
    refetchOnWindowFocus: true,
  })
  const trials = trialsData != null ? ensureArray(trialsData as Trial[] | { results: Trial[] }) : []

  const { data: fullDetail, isLoading: loadingFull } = useQuery({
    queryKey: ['trial-full', trialId],
    queryFn: () => trialsApi.getFull(trialId!),
    enabled: trialId != null && user?.role_names?.some((r) => r.toLowerCase() === 'judge'),
  })

  const createVerdict = useMutation({
    mutationFn: (data: {
      trial: number
      verdict_type: 'guilty' | 'innocent'
      title?: string
      description?: string
      punishment_title?: string
      punishment_description?: string
    }) => verdictsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['trials'] })
      qc.invalidateQueries({ queryKey: ['trial-full', trialId] })
      navigate('/dashboard/trials')
    },
  })

  if (trialId != null && isJudge) {
    if (loadingFull || (fullDetail == null && trialId != null)) {
      return (
        <div className="space-y-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard/trials')}>← Back to trials</Button>
          <Skeleton className="h-96 w-full" />
        </div>
      )
    }
    if (!fullDetail) {
      return (
        <div>
          <p className="text-red-400">Trial not found.</p>
          <Button variant="ghost" onClick={() => navigate('/dashboard/trials')}>Back</Button>
        </div>
      )
    }
    const trial = fullDetail as TrialFullDetail
    const hasVerdict = false // could check trial.verdict from API if we had it

    return (
      <div className="space-y-6">
        <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard/trials')}>← Back to trials</Button>
        <h1 className="text-2xl font-bold text-slate-100">Trial — Full case data (Judge)</h1>

        <Card>
          <CardHeader>
            <CardTitle>Case</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p><strong>Title:</strong> {trial.case_data?.title}</p>
            <p><strong>Description:</strong> {trial.case_data?.description || '—'}</p>
            <p><strong>Status:</strong> {trial.case_data?.status?.replace(/_/g, ' ')}</p>
            <p><strong>Severity:</strong> {trial.case_data?.severity}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Evidence ({trial.evidence_items?.length ?? 0})</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {(trial.evidence_items ?? []).map((e: { id: number; title: string; evidence_type: string }) => (
                <li key={e.id}>[{e.evidence_type}] {e.title}</li>
              ))}
              {(trial.evidence_items?.length ?? 0) === 0 && <li className="text-slate-500">No evidence</li>}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Personnel</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {(trial.personnel ?? []).map((p: { id: number; username: string; full_name: string; role_names: string[] }) => (
                <li key={p.id}>{p.full_name || p.username} — {p.role_names?.join(', ')}</li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Record verdict</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Verdict</label>
              <select
                value={verdictType}
                onChange={(e) => setVerdictType(e.target.value as 'guilty' | 'innocent')}
                className="rounded-md border border-slate-600 bg-slate-800 text-slate-200 px-3 py-2"
              >
                <option value="guilty">Guilty</option>
                <option value="innocent">Innocent</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Verdict title (optional)</label>
              <input
                value={verdictTitle}
                onChange={(e) => setVerdictTitle(e.target.value)}
                className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Verdict description (optional)</label>
              <textarea
                value={verdictDescription}
                onChange={(e) => setVerdictDescription(e.target.value)}
                className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-slate-200 min-h-[60px]"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Punishment title</label>
              <input
                value={punishmentTitle}
                onChange={(e) => setPunishmentTitle(e.target.value)}
                className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Punishment description</label>
              <textarea
                value={punishmentDescription}
                onChange={(e) => setPunishmentDescription(e.target.value)}
                className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-slate-200 min-h-[80px]"
              />
            </div>
            <Button
              onClick={() =>
                createVerdict.mutate({
                  trial: trialId!,
                  verdict_type: verdictType,
                  title: verdictTitle || undefined,
                  description: verdictDescription || undefined,
                  punishment_title: punishmentTitle || undefined,
                  punishment_description: punishmentDescription || undefined,
                })
              }
              loading={createVerdict.isPending}
            >
              Record verdict
            </Button>
            {createVerdict.isError && (
              <p className="text-sm text-red-400">{getApiErrorMessage(createVerdict.error)}</p>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Trials</h1>
      <p className="text-slate-400">Cases referred to court (after captain decision GUILTY). Open a trial to view full case data and record verdict.</p>
      {!isJudge && (
        <Card><CardContent className="py-12 text-center text-slate-500">Only users with the Judge role can view and manage trials.</CardContent></Card>
      )}
      {isJudge && trialsLoading && <Skeleton className="h-32 w-full" />}
      {isJudge && trialsError && (
        <p className="text-red-400">Failed to load trials. You may need the Judge role.</p>
      )}
      {isJudge && !trialsLoading && trials.length === 0 && !trialsError && (
        <Card><CardContent className="py-12 text-center text-slate-500">No trials yet. Trials are created when a captain decides GUILTY (and chief approves for CRITICAL cases). After a captain marks a suspect GUILTY, the case is referred to court and appears here.</CardContent></Card>
      )}
      {isJudge && trials.length > 0 && (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {trials.map((t) => (
          <Card key={t.id}>
            <CardHeader>
              <CardTitle className="text-base">Case #{t.case}</CardTitle>
              <p className="text-sm text-slate-500">{t.case_title}</p>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm text-slate-400">Judge: {t.judge_username ?? '—'}</p>
              <p className="text-xs text-slate-600">{formatDate(t.started_at)}</p>
              {isJudge && (
                <Button
                  size="sm"
                  onClick={() => navigate(`/dashboard/trials/${t.id}`)}
                >
                  View full case & record verdict
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      )}
    </div>
  )
}
