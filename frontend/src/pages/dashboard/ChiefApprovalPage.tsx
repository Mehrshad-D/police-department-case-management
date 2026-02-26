import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { captainDecisionsApi, chiefApprovalApi } from '@/api/endpoints'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { getApiErrorMessage } from '@/api/client'
import type { CaptainDecision } from '@/types'

const SEVERITY_CRISIS = 0

export function ChiefApprovalPage() {
  const qc = useQueryClient()
  const [comment, setComment] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [status, setStatus] = useState<'approved' | 'rejected'>('approved')
  const [successReferred, setSuccessReferred] = useState(false)

  const { data: decisionsData } = useQuery({
    queryKey: ['captain-decisions'],
    queryFn: () => captainDecisionsApi.list({}),
  })
  const decisions = Array.isArray(decisionsData) ? decisionsData : []
  const pendingChief = decisions.filter(
    (d: CaptainDecision & { case_severity?: number; has_chief_approval?: boolean }) =>
      d.case_severity === SEVERITY_CRISIS && !d.has_chief_approval
  )

  const submitApproval = useMutation({
    mutationFn: ({ id, status, comment }: { id: number; status: 'approved' | 'rejected'; comment?: string }) =>
      chiefApprovalApi.create(id, { status, comment }),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['captain-decisions'] })
      qc.invalidateQueries({ queryKey: ['trials'] })
      setSelectedId(null)
      if (variables.status === 'approved') {
        setSuccessReferred(true)
        setTimeout(() => setSuccessReferred(false), 8000)
      }
    },
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Chief Approval</h1>
      <p className="text-slate-400">CRITICAL severity cases require your approval of the captain decision.</p>
      {successReferred && (
        <Card className="border-emerald-600 bg-emerald-950/40">
          <CardContent className="py-4">
            <p className="text-emerald-200">
              <strong>Approval applied.</strong> The case has been referred to court. A trial has been created and will appear in the <strong>Trials</strong> list for the Judge.
            </p>
          </CardContent>
        </Card>
      )}
      {pendingChief.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">No captain decisions pending chief approval.</CardContent>
        </Card>
      )}
      {pendingChief.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {pendingChief.map((d: CaptainDecision & { reasoning?: string }) => (
            <Card key={d.id}>
              <CardHeader>
                <CardTitle className="text-base">Case #{d.case} · Suspect #{d.suspect}</CardTitle>
                <p className="text-sm text-slate-500">Decision: {d.final_decision.toUpperCase()}</p>
                {d.reasoning && <p className="text-sm text-slate-400">{d.reasoning}</p>}
              </CardHeader>
              <CardContent>
                {selectedId === d.id ? (
                  <div className="space-y-2">
                    <textarea
                      placeholder="Comment (optional)"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      className="w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 text-sm text-slate-200 min-h-[60px]"
                    />
                    <div className="flex gap-2">
                      <Button size="sm" variant="secondary" onClick={() => setStatus('rejected')}>
                        Reject
                      </Button>
                      <Button size="sm" onClick={() => setStatus('approved')}>
                        Approve
                      </Button>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => submitApproval.mutate({ id: d.id, status, comment })}
                      loading={submitApproval.isPending}
                      disabled={submitApproval.isPending}
                    >
                      Submit
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setSelectedId(null)}>
                      Cancel
                    </Button>
                    {submitApproval.isError && (
                      <p className="text-sm text-red-400">{getApiErrorMessage(submitApproval.error)}</p>
                    )}
                  </div>
                ) : (
                  <Button size="sm" onClick={() => setSelectedId(d.id)}>
                    Approve / Reject
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
