import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useCase, useCaseUpdate, useCaseSubmitSuspectsToSergeant } from '@/hooks/useCases'
import { useSuspectsList, useSuspectPropose, useSuspectSupervisorReview } from '@/hooks/useSuspects'
import { usersApi, interrogationsApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/authStore'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'
import type { Suspect, Interrogation } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data as { results: T[] }).results ?? []
}

const SEVERITY_MAP: Record<number, string> = {
  3: 'Level 3 - Minor',
  2: 'Level 2 - Moderate',
  1: 'Level 1 - Major',
  0: 'Crisis',
}

const STATUS_WAITING_SERGEANT = 'waiting_sergeant_approval'
const STATUS_UNDER_INVESTIGATION = 'under_investigation'
const STATUS_ARRESTED = 'arrested'

export function CaseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const caseId = id ? parseInt(id, 10) : null
  const { data: caseData, isLoading, error } = useCase(caseId)
  const [selectedDetectiveId, setSelectedDetectiveId] = useState<number | ''>('')
  const [selectedSeverity, setSelectedSeverity] = useState<number>(3)
  const [addSuspectUserId, setAddSuspectUserId] = useState<number | ''>('')
  const [rejectMessage, setRejectMessage] = useState<Record<number, string>>({})
  const [detectiveScore, setDetectiveScore] = useState<Record<number, number>>({})
  const [sergeantScore, setSergeantScore] = useState<Record<number, number>>({})

  const { data: detectivesData } = useQuery({
    queryKey: ['detectives'],
    queryFn: () => usersApi.listDetectives(),
  })
  const detectives = Array.isArray(detectivesData) ? detectivesData : []
  const { data: suspectsData } = useSuspectsList(caseId != null ? { case: caseId } : undefined)
  const suspects = suspectsData ? ensureArray(suspectsData as Suspect[] | { results: Suspect[] }) : []
  const { data: usersList = [] } = useQuery({
    queryKey: ['users', 'suspect-candidates'],
    queryFn: () => usersApi.listSuspectCandidates(),
  })

  const updateCase = useCaseUpdate(caseId ?? 0)
  const submitToSergeant = useCaseSubmitSuspectsToSergeant(caseId ?? 0)
  const proposeSuspect = useSuspectPropose()
  const supervisorReview = useSuspectSupervisorReview()
  const qc = useQueryClient()
  const { data: interrogationsData } = useQuery({
    queryKey: ['interrogations', caseId],
    queryFn: () => interrogationsApi.list({ case: caseId ?? undefined }),
    enabled: caseId != null,
  })
  const interrogationsList = interrogationsData
    ? Array.isArray(interrogationsData)
      ? interrogationsData
      : (interrogationsData as { results?: Interrogation[] }).results ?? []
    : []
  const createInterrogation = useMutation({
    mutationFn: (suspectId: number) => interrogationsApi.create({ suspect: suspectId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['interrogations'] }),
  })
  const submitDetectiveScore = useMutation({
    mutationFn: ({ id, guilt_score, notes }: { id: number; guilt_score: number; notes?: string }) =>
      interrogationsApi.submitDetectiveScore(id, { guilt_score, notes }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['interrogations'] }),
  })
  const submitSergeantScore = useMutation({
    mutationFn: ({ id, guilt_score, notes }: { id: number; guilt_score: number; notes?: string }) =>
      interrogationsApi.submitSergeantScore(id, { guilt_score, notes }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['interrogations'] }),
  })

  const isDetective = user?.role_names?.some((r) => r.toLowerCase() === 'detective')
  const isSergeant = user?.role_names?.some((r) => r.toLowerCase() === 'sergeant')
  const canSubmitToSergeant =
    isDetective &&
    caseId != null &&
    (caseData?.status === 'open' || caseData?.status === STATUS_UNDER_INVESTIGATION) &&
    caseData?.status !== STATUS_WAITING_SERGEANT &&
    suspects.some(
      (s) => s.status === STATUS_UNDER_INVESTIGATION && s.approved_by_supervisor == null
    )
  const pendingSuspects = suspects.filter(
    (s) => s.status === STATUS_UNDER_INVESTIGATION && s.approved_by_supervisor == null
  )

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

          {/* Suspects */}
          <div className="mt-6 pt-6 border-t border-slate-700">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
              <CardTitle className="text-base">Suspects</CardTitle>
              {canSubmitToSergeant && (
                <Button
                  size="sm"
                  onClick={() => submitToSergeant.mutate()}
                  loading={submitToSergeant.isPending}
                  disabled={pendingSuspects.length === 0}
                >
                  Submit suspects to sergeant
                </Button>
              )}
            </div>
            {caseData?.status === STATUS_WAITING_SERGEANT && (
              <p className="text-amber-400 text-sm mb-2">Waiting for sergeant to review suspects.</p>
            )}
            {/* Add suspect (detective) */}
            {isDetective && caseId != null && caseData?.status !== STATUS_WAITING_SERGEANT && (
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <select
                  value={addSuspectUserId === '' ? '' : addSuspectUserId}
                  onChange={(e) => setAddSuspectUserId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="rounded-md border border-slate-600 bg-slate-800 text-slate-200 px-3 py-2 text-sm min-w-[200px]"
                >
                  <option value="">— Add suspect (select user) —</option>
                  {usersList.map((u: { id: number; username: string; full_name?: string }) => (
                    <option key={u.id} value={u.id} disabled={suspects.some((s) => s.user === u.id)}>
                      {u.full_name || u.username} {suspects.some((s) => s.user === u.id) ? '(already suspect)' : ''}
                    </option>
                  ))}
                </select>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    if (addSuspectUserId !== '') {
                      proposeSuspect.mutate({ caseId, userId: addSuspectUserId })
                      setAddSuspectUserId('')
                    }
                  }}
                  loading={proposeSuspect.isPending}
                  disabled={addSuspectUserId === ''}
                >
                  Add suspect
                </Button>
              </div>
            )}
            {proposeSuspect.isError && (
              <p className="text-sm text-red-400 mb-2">{getApiErrorMessage(proposeSuspect.error)}</p>
            )}
            {submitToSergeant.isError && (
              <p className="text-sm text-red-400 mb-2">{getApiErrorMessage(submitToSergeant.error)}</p>
            )}
            <ul className="space-y-2">
              {suspects.length === 0 && <li className="text-slate-500 text-sm">No suspects added yet.</li>}
              {suspects.map((s) => (
                <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-slate-800/50 px-3 py-2">
                  <div>
                    <span className="font-medium text-slate-200">{s.user_full_name || s.user_username}</span>
                    <span className="ml-2 rounded px-1.5 py-0.5 text-xs bg-slate-700 text-slate-400">
                      {s.status.replace(/_/g, ' ')}
                    </span>
                    {s.rejection_message && (
                      <p className="text-amber-400 text-xs mt-1">Rejection: {s.rejection_message}</p>
                    )}
                  </div>
                  {isSergeant &&
                    s.status === STATUS_UNDER_INVESTIGATION &&
                    s.approved_by_supervisor == null &&
                    caseData?.status === STATUS_WAITING_SERGEANT && (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          placeholder="Rejection message (optional)"
                          value={rejectMessage[s.id] ?? ''}
                          onChange={(e) => setRejectMessage((prev) => ({ ...prev, [s.id]: e.target.value }))}
                          className="rounded border border-slate-600 bg-slate-800 text-slate-200 px-2 py-1 text-sm w-48"
                        />
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() =>
                            supervisorReview.mutate({ id: s.id, action: 'reject', rejection_message: rejectMessage[s.id] })
                          }
                          loading={supervisorReview.isPending}
                        >
                          Reject
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => supervisorReview.mutate({ id: s.id, action: 'approve' })}
                          loading={supervisorReview.isPending}
                        >
                          Approve (arrest)
                        </Button>
                      </div>
                    )}
                </li>
              ))}
            </ul>
          </div>

          {/* Interrogation panel (arrested suspects) */}
          {suspects.filter((s) => s.status === STATUS_ARRESTED).length > 0 && (
            <div className="mt-6 pt-6 border-t border-slate-700">
              <CardTitle className="text-base mb-3">Interrogation (guilt score 1–10)</CardTitle>
              <p className="text-slate-500 text-sm mb-4">
                Detective and Sergeant each assign a score. Only the assigned detective and a Sergeant can submit.
              </p>
              {suspects
                .filter((s) => s.status === STATUS_ARRESTED)
                .map((s) => {
                  const interrogation = interrogationsList.find((i: Interrogation) => i.suspect === s.id)
                  return (
                    <div key={s.id} className="rounded-lg bg-slate-800/50 p-4 mb-4">
                      <p className="font-medium text-slate-200 mb-2">{s.user_full_name || s.user_username}</p>
                      {!interrogation ? (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => createInterrogation.mutate(s.id)}
                          loading={createInterrogation.isPending}
                        >
                          Start interrogation
                        </Button>
                      ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                          {/* Detective score: only assigned detective can set; sergeant sees read-only */}
                          <div>
                            <label className="block text-sm text-slate-400 mb-1">Detective score (1–10)</label>
                            {isDetective && caseData?.assigned_detective === user?.id ? (
                              <>
                                <input
                                  type="range"
                                  min={1}
                                  max={10}
                                  value={interrogation.detective_probability ?? detectiveScore[interrogation.id] ?? 5}
                                  onChange={(e) => setDetectiveScore((p) => ({ ...p, [interrogation.id]: Number(e.target.value) }))}
                                  disabled={interrogation.detective_probability != null}
                                  className="w-full"
                                />
                                <span className="text-slate-200 ml-2">{interrogation.detective_probability ?? detectiveScore[interrogation.id] ?? '—'}</span>
                                {interrogation.detective_probability == null && (
                                  <Button
                                    size="sm"
                                    className="mt-1"
                                    onClick={() =>
                                      submitDetectiveScore.mutate({
                                        id: interrogation.id,
                                        guilt_score: detectiveScore[interrogation.id] ?? 5,
                                      })
                                    }
                                    loading={submitDetectiveScore.isPending}
                                  >
                                    Submit my score
                                  </Button>
                                )}
                              </>
                            ) : (
                              <p className="text-slate-200">{interrogation.detective_probability != null ? interrogation.detective_probability : '—'}</p>
                            )}
                          </div>
                          {/* Sergeant score: only sergeant can set; detective sees read-only */}
                          <div>
                            <label className="block text-sm text-slate-400 mb-1">Sergeant score (1–10)</label>
                            {isSergeant ? (
                              <>
                                <input
                                  type="range"
                                  min={1}
                                  max={10}
                                  value={interrogation.supervisor_probability ?? sergeantScore[interrogation.id] ?? 5}
                                  onChange={(e) => setSergeantScore((p) => ({ ...p, [interrogation.id]: Number(e.target.value) }))}
                                  disabled={interrogation.supervisor_probability != null}
                                  className="w-full"
                                />
                                <span className="text-slate-200 ml-2">{interrogation.supervisor_probability ?? sergeantScore[interrogation.id] ?? '—'}</span>
                                {interrogation.supervisor_probability == null && (
                                  <Button
                                    size="sm"
                                    className="mt-1"
                                    onClick={() =>
                                      submitSergeantScore.mutate({
                                        id: interrogation.id,
                                        guilt_score: sergeantScore[interrogation.id] ?? 5,
                                      })
                                    }
                                    loading={submitSergeantScore.isPending}
                                  >
                                    Submit my score
                                  </Button>
                                )}
                              </>
                            ) : (
                              <p className="text-slate-200">{interrogation.supervisor_probability != null ? interrogation.supervisor_probability : '—'}</p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
