import { useState } from 'react'
import { rewardsApi } from '@/api/endpoints'
import { Button } from '@/components/ui/Button'

export function RewardClaimPage() {
  const [nationalId, setNationalId] = useState('')
  const [code, setCode] = useState('')
  const [result, setResult] = useState<any>(null)

  const handleSubmit = async () => {
    try {
      const res = await rewardsApi.claim({
        national_id: nationalId,
        code,
      })
      setResult(res.data.data)
    } catch (e: any) {
      alert(e.response?.data?.error?.message || 'Error')
    }
  }

  return (
    <div className="p-8 text-white">
      <h1 className="text-2xl mb-6">Reward Claim</h1>

      <input
        className="block mb-3 p-2 text-black"
        placeholder="National ID"
        value={nationalId}
        onChange={(e) => setNationalId(e.target.value)}
      />

      <input
        className="block mb-3 p-2 text-black"
        placeholder="Reward Code"
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />

      <Button onClick={handleSubmit}>Check & Claim</Button>

      {result && (
        <div className="mt-6">
          <p><strong>Amount:</strong> {result.reward.amount_rials}</p>
          <p><strong>Citizen:</strong> {result.citizen_username}</p>
          <p><strong>Claimed:</strong> {result.reward.claimed ? 'Yes' : 'No'}</p>
        </div>
      )}
    </div>
  )
}