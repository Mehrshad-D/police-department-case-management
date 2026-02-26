import { useEffect, useState } from 'react'
import { tipsApi } from '@/api/endpoints'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { useAuthStore } from '@/store/authStore'

export function TipsPage() {
  const [tips, setTips] = useState<any[]>([])
  const user = useAuthStore((s) => s.user)

  const loadTips = async () => {
    const res = await tipsApi.list()
    setTips(res.data)
  }

  useEffect(() => {
    loadTips()
  }, [])

  const handleOfficerReview = async (id: number) => {
    await tipsApi.officerReview(id)
    loadTips()
  }

  const handleDetectiveConfirm = async (id: number) => {
    const amount = prompt('Enter reward amount (rials):')
    if (!amount) return
    await tipsApi.detectiveConfirm(id, Number(amount))
    loadTips()
  }

  return (
    <div className="p-8 text-white">
      <h1 className="text-2xl mb-6">Tips</h1>

      {tips.map((tip) => (
        <Card key={tip.id} className="mb-4">
          <CardContent className="p-4 space-y-2">
            <p><strong>Title:</strong> {tip.title}</p>
            <p><strong>Status:</strong> {tip.status}</p>
            <p><strong>Submitted by:</strong> {tip.submitter_username}</p>

            {/* Officer button */}
            {user?.role_names?.some(
                (r) => r.toLowerCase() === 'police officer') &&
              tip.status === 'pending' && (
                <Button onClick={() => handleOfficerReview(tip.id)}>
                  Review & Forward
                </Button>
              )}

            {/* Detective button */}
            {user?.role_names?.some(
                (r) => r.toLowerCase() === 'Detective') &&
              tip.status === 'officer_reviewed' && (
                <Button onClick={() => handleDetectiveConfirm(tip.id)}>
                  Confirm & Create Reward
                </Button>
              )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}