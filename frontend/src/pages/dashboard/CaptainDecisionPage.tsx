import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { captainDecisionsApi, interrogationsApi } from '@/api/endpoints'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { getApiErrorMessage } from '@/api/client'
import type { Interrogation } from '@/types'

function ensureArray<T>(x: T[] | { results: T[] }): T[] {
  return Array.isArray(x) ? x : (x as { results: T[] }).results ?? []
}

type SuccessMessage = { type: 'referred' } | { type: 'chief_required' } | { type: 'released' }

export function CaptainDecisionPage() {
  const qc = useQueryClient()
  const [reasoning, setReasoning] = useState('')
  const [selectedDecision, setSelectedDecision] = useState<{ suspectId: number; caseId: number } | null>(null)
  const [decision, setDecision] = useState<'guilty' | 'not_guilty'>('not_guilty')
  const [successMessage, setSuccessMessage] = useState<SuccessMessage | null>(null)

  const { data: interrogationsData } = useQuery({
    queryKey: ['interrogations', 'all'],
    queryFn: () => interrogationsApi.list({}),
  })
  const interrogations = interrogationsData ? ensureArray(interrogationsData as Interrogation[] | { results: Interrogation[] }) : []
  const readyForCaptain = interrogations.filter(
    (i) => i.detective_probability != null && i.supervisor_probability != null
  )

  const createDecision = useMutation({
    mutationFn: (payload: { suspect_id: number; case_id: number; final_decision: 'guilty' | 'not_guilty'; reasoning?: string }) =>
      captainDecisionsApi.create(payload),
    onSuccess: (response: { success?: boolean; data?: unknown; requires_chief_approval?: boolean }, variables) => {
      qc.invalidateQueries({ queryKey: ['captain-decisions'] })
      qc.invalidateQueries({ queryKey: ['interrogations'] })
      qc.invalidateQueries({ queryKey: ['trials'] })
      setSelectedDecision(null)
      if (response?.requires_chief_approval) {
        setSuccessMessage({ type: 'chief_required' })
      } else if (variables.final_decision === 'guilty') {
        setSuccessMessage({ type: 'referred' })
      } else {
        setSuccessMessage({ type: 'released' })
      }
      setTimeout(() => setSuccessMessage(null), 8000)
    },
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Captain Decision</h1>
      <p className="text-slate-400">
        Suspects with both detective and sergeant scores are listed below. Make final decision (GUILTY / NOT GUILTY). CRITICAL cases require Chief approval.
      </p>
      {successMessage && (
        <Card className={successMessage.type === 'referred' ? 'border-emerald-600 bg-emerald-950/40' : successMessage.type === 'chief_required' ? 'border-amber-600 bg-amber-950/40' : 'border-slate-600'}>
          <CardContent className="py-4">
            {successMessage.type === 'referred' && (
              <p className="text-emerald-200">
                <strong>Case referred to court.</strong> A trial has been created and will appear in the <strong>Trials</strong> list for the Judge. The judge can open the trial, review the full case, and record a verdict.
              </p>
            )}
            {successMessage.type === 'chief_required' && (
              <p className="text-amber-200">
                <strong>Decision recorded.</strong> This is a CRITICAL case — Chief approval is required before the case is referred to court. After the Chief approves, a trial will be created for the Judge.
              </p>
            )}
            {successMessage.type === 'released' && (
              <p className="text-slate-300">
                <strong>Decision recorded.</strong> Suspect marked NOT GUILTY and released. Case remains in your workflow as needed.
              </p>
            )}
          </CardContent>
        </Card>
      )}
      {readyForCaptain.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">No interrogations ready for captain decision (need both scores).</CardContent>
        </Card>
      )}
      {readyForCaptain.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {readyForCaptain.map((inter) => (
            <Card key={inter.id}>
              <CardHeader>
                <CardTitle className="text-base">Suspect #{inter.suspect}</CardTitle>
                <p className="text-sm text-slate-500">
                  Detective: {inter.detective_probability} · Sergeant: {inter.supervisor_probability}
                </p>
              </CardHeader>
              <CardContent>
                {selectedDecision?.suspectId === inter.suspect ? (
                  <div className="space-y-2">
                    <textarea
                      placeholder="Reasoning (optional)"
                      value={reasoning}
                      onChange={(e) => setReasoning(e.target.value)}
                      className="w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 text-sm text-slate-200 min-h-[60px]"
                    />
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setDecision('not_guilty')}
                      >
                        NOT GUILTY
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => setDecision('guilty')}
                      >
                        GUILTY
                      </Button>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => {
                        createDecision.mutate({
                          suspect_id: inter.suspect,
                          case_id: selectedDecision.caseId,
                          final_decision: decision,
                          reasoning,
                        })
                      }}
                      loading={createDecision.isPending}
                    >
                      Submit decision
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setSelectedDecision(null)}>
                      Cancel
                    </Button>
                  </div>
                ) : (
                  <Button
                    size="sm"
                    onClick={() => setSelectedDecision({ suspectId: inter.suspect, caseId: inter.case_id ?? 0 })}
                  >
                    Make decision
                  </Button>
                )}
                {createDecision.isError && (
                  <p className="text-sm text-red-400">{getApiErrorMessage(createDecision.error)}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
