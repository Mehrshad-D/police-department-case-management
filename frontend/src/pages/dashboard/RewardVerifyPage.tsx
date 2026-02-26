import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { rewardsApi } from '@/api/endpoints'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { formatDate, formatCurrencyRials } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'
import type { RewardVerifyResponse } from '@/types'

export function RewardVerifyPage() {
  const [nationalId, setNationalId] = useState('')
  const [code, setCode] = useState('')
  const [result, setResult] = useState<RewardVerifyResponse | null>(null)
  const [error, setError] = useState('')

  const verify = useMutation({
    mutationFn: () => rewardsApi.verify(nationalId, code),
    onSuccess: (data) => {
      setResult(data)
      setError('')
    },
    onError: (e) => {
      setError(getApiErrorMessage(e))
      setResult(null)
    },
  })

  const redeem = useMutation({
    mutationFn: () => rewardsApi.redeem(nationalId, code),
    onSuccess: () => {
      setResult((prev) => (prev ? { ...prev, payment_status: 'paid' as const } : null))
    },
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Reward Verification</h1>
      <p className="text-slate-400">Enter national ID and reward code to verify and mark payment.</p>
      <Card>
        <CardHeader>
          <CardTitle>Verify reward</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder="National ID"
            value={nationalId}
            onChange={(e) => setNationalId(e.target.value)}
          />
          <Input
            placeholder="Reward code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
          <Button
            onClick={() => verify.mutate()}
            loading={verify.isPending}
            disabled={!nationalId.trim() || !code.trim()}
          >
            Verify
          </Button>
          {error && <p className="text-sm text-red-400">{error}</p>}
        </CardContent>
      </Card>
      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Reward details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {result.user_info && (
              <p className="text-slate-300">
                User: {result.user_info.full_name || result.user_info.username} ({result.user_info.national_id})
              </p>
            )}
            <p className="text-slate-300">Amount: {formatCurrencyRials(result.reward_amount)}</p>
            {result.case_info && <p className="text-slate-300">Case: #{result.case_info.id} — {result.case_info.title}</p>}
            {result.suspect_info && <p className="text-slate-300">Suspect: #{result.suspect_info.id}</p>}
            <p className="text-slate-300">Payment status: <span className={result.payment_status === 'paid' ? 'text-green-400' : 'text-amber-400'}>{result.payment_status}</span></p>
            {result.payment_record && (
              <p className="text-slate-500 text-sm">Paid at: {formatDate(result.payment_record.paid_at)}</p>
            )}
            {result.payment_status === 'unpaid' && (
              <Button
                onClick={() => redeem.mutate()}
                loading={redeem.isPending}
              >
                Mark as paid
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
