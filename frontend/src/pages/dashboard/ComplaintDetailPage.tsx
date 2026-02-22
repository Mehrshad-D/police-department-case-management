import { useParams, useNavigate } from 'react-router-dom'
import { useComplaint } from '@/hooks/useComplaints'
import { useComplaintTraineeReview, useComplaintOfficerReview } from '@/hooks/useComplaints'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'

export function ComplaintDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const complaintId = id ? parseInt(id, 10) : null
  const { data: complaint, isLoading, error } = useComplaint(complaintId)
  const traineeReview = useComplaintTraineeReview()
  const officerReview = useComplaintOfficerReview()

  if (error || (complaintId && !isLoading && !complaint)) {
    return (
      <div>
        <p className="text-red-400">Complaint not found.</p>
        <Button variant="ghost" onClick={() => navigate('/dashboard/complaints')}>Back</Button>
      </div>
    )
  }

  if (isLoading || !complaint) {
    return <Skeleton className="h-64 w-full" />
  }

  const canTraineeReview = complaint.status === 'pending_trainee'
  const canOfficerReview = complaint.status === 'pending_officer'

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard/complaints')}>← Back</Button>
      <Card>
        <CardHeader>
          <CardTitle>{complaint.title}</CardTitle>
          <span className="text-sm text-slate-500">{complaint.status.replace(/_/g, ' ')} · By {complaint.complainant_username}</span>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-slate-300">{complaint.description}</p>
          {complaint.last_correction_message && (
            <p className="text-amber-400 text-sm">Correction message: {complaint.last_correction_message}</p>
          )}
          <p className="text-xs text-slate-600">Created {formatDate(complaint.created_at)} · Corrections: {complaint.correction_count}</p>

          {canTraineeReview && (
            <div className="flex gap-2 pt-4 border-t border-slate-700">
              <Button size="sm" onClick={() => traineeReview.mutate({ id: complaint.id, action: 'approve' })} loading={traineeReview.isPending}>
                Approve (forward to officer)
              </Button>
              <Button variant="danger" size="sm" onClick={() => {
                const msg = window.prompt('Correction message for complainant')
                traineeReview.mutate({ id: complaint.id, action: 'return_correction', correction_message: msg ?? '' })
              }} loading={traineeReview.isPending}>
                Return for correction
              </Button>
            </div>
          )}
          {canOfficerReview && (
            <div className="flex gap-2 pt-4 border-t border-slate-700">
              <Button size="sm" onClick={() => officerReview.mutate({ id: complaint.id, action: 'approve' })} loading={officerReview.isPending}>
                Approve (create case)
              </Button>
              <Button variant="secondary" size="sm" onClick={() => officerReview.mutate({ id: complaint.id, action: 'send_back' })} loading={officerReview.isPending}>
                Send back to trainee
              </Button>
            </div>
          )}
          {(traineeReview.isError || officerReview.isError) && (
            <p className="text-sm text-red-400">{getApiErrorMessage(traineeReview.error || officerReview.error)}</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
