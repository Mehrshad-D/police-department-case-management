import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tipsApi, rewardsApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/authStore'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { formatDate } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'
import type { Tip, Reward } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data as { results: T[] }).results ?? []
}

export function TipsPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [lookupNationalId, setLookupNationalId] = useState('')
  const [lookupCode, setLookupCode] = useState('')
  const [lookupResult, setLookupResult] = useState<Reward | null>(null)
  const [lookupError, setLookupError] = useState('')

  const { data: tipsData, isLoading } = useQuery({
    queryKey: ['tips'],
    queryFn: () => tipsApi.list(),
  })
  const tips = tipsData ? ensureArray(tipsData as Tip[] | { results: Tip[] }) : []

  const createTip = useMutation({
    mutationFn: (data: { title: string; description: string }) => tipsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tips'] })
      setTitle('')
      setDescription('')
    },
  })

  const officerReview = useMutation({
    mutationFn: ({
      id,
      action,
      message,
    }: { id: number; action: 'approve' | 'reject'; message?: string }) =>
      tipsApi.officerReview(id, action, message),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tips'] }),
  })

  const detectiveConfirm = useMutation({
    mutationFn: ({ id, amount_rials }: { id: number; amount_rials?: number }) =>
      tipsApi.detectiveConfirm(id, amount_rials),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['tips'] })
      if (data?.reward_code) alert(`Reward code for user: ${data.reward_code}`)
    },
  })

  const redeemReward = useMutation({
    mutationFn: ({ national_id, code }: { national_id: string; code: string }) =>
      rewardsApi.redeem(national_id, code),
    onSuccess: () => {
      setLookupResult(null)
      setLookupCode('')
      setLookupNationalId('')
      setLookupError('')
      qc.invalidateQueries({ queryKey: ['tips'] })
    },
  })

  const handleLookup = async () => {
    setLookupError('')
    setLookupResult(null)
    try {
      const r = await rewardsApi.lookup(lookupNationalId, lookupCode)
      setLookupResult(r)
    } catch (e: unknown) {
      setLookupError(getApiErrorMessage(e))
    }
  }

  const isOfficer = user?.role_names?.some((r) => r.toLowerCase() === 'police officer' || r.toLowerCase() === 'sergeant')
  const isDetective = user?.role_names?.some((r) => r.toLowerCase() === 'detective')
  const canReview = isOfficer || user?.role_names?.some((r) => r.toLowerCase() === 'system administrator')
  const canRedeem = isOfficer || isDetective || user?.role_names?.some((r) => ['Sergeant', 'Captain', 'Police Chief', 'System Administrator'].includes(r))

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-100">Tips & Rewards</h1>

      {/* Submit tip (citizens / any user) */}
      <Card>
        <CardHeader>
          <CardTitle>Submit a tip</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <textarea
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-slate-200 min-h-[80px]"
          />
          <Button
            onClick={() => createTip.mutate({ title, description })}
            loading={createTip.isPending}
            disabled={!title.trim() || !description.trim()}
          >
            Submit tip
          </Button>
          {createTip.isError && (
            <p className="text-sm text-red-400">{getApiErrorMessage(createTip.error)}</p>
          )}
        </CardContent>
      </Card>

      {/* Reward lookup & redeem (police) */}
      {canRedeem && (
        <Card>
          <CardHeader>
            <CardTitle>Reward lookup / Redeem at office</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Input
                placeholder="National ID"
                value={lookupNationalId}
                onChange={(e) => setLookupNationalId(e.target.value)}
                className="max-w-[200px]"
              />
              <Input
                placeholder="Reward code"
                value={lookupCode}
                onChange={(e) => setLookupCode(e.target.value)}
                className="max-w-[200px]"
              />
              <Button variant="secondary" onClick={handleLookup} disabled={!lookupNationalId || !lookupCode}>
                Lookup
              </Button>
              <Button
                onClick={() => redeemReward.mutate({ national_id: lookupNationalId, code: lookupCode })}
                loading={redeemReward.isPending}
                disabled={!lookupResult || lookupResult.claimed}
              >
                Mark redeemed
              </Button>
            </div>
            {lookupError && <p className="text-sm text-red-400">{lookupError}</p>}
            {lookupResult && (
              <div className="rounded bg-slate-800 p-3 text-sm">
                <p>Amount: {lookupResult.amount_rials} Rials</p>
                <p>Claimed: {lookupResult.claimed ? 'Yes' : 'No'}</p>
                {lookupResult.claimed_at && <p>Claimed at: {formatDate(lookupResult.claimed_at)}</p>}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* List tips */}
      <Card>
        <CardHeader>
          <CardTitle>Tips</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && <p className="text-slate-500">Loading…</p>}
          {!isLoading && tips.length === 0 && <p className="text-slate-500">No tips.</p>}
          {!isLoading && tips.length > 0 && (
            <ul className="space-y-3">
              {tips.map((t) => (
                <li key={t.id} className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-medium text-slate-200">{t.title}</p>
                      <p className="text-sm text-slate-500">by {t.submitter_username} · {formatDate(t.created_at)}</p>
                      <p className="text-slate-400 mt-1">{t.description}</p>
                      <span className="inline-block mt-2 rounded px-2 py-0.5 text-xs bg-slate-700 text-slate-400">
                        {t.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    {canReview && t.status === 'pending' && (
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => officerReview.mutate({ id: t.id, action: 'reject' })}
                          loading={officerReview.isPending}
                        >
                          Reject
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => officerReview.mutate({ id: t.id, action: 'approve' })}
                          loading={officerReview.isPending}
                        >
                          Send to detective
                        </Button>
                      </div>
                    )}
                    {isDetective && t.status === 'officer_reviewed' && (
                      <Button
                        size="sm"
                        onClick={() => detectiveConfirm.mutate({ id: t.id })}
                        loading={detectiveConfirm.isPending}
                      >
                        Accept & generate reward code
                      </Button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
