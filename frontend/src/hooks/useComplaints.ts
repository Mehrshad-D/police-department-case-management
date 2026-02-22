import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { complaintsApi } from '@/api/endpoints'

export function useComplaintsList() {
  return useQuery({
    queryKey: ['complaints'],
    queryFn: () => complaintsApi.list(),
  })
}

export function useComplaint(id: number | null) {
  return useQuery({
    queryKey: ['complaint', id],
    queryFn: () => complaintsApi.get(id!),
    enabled: id != null,
  })
}

export function useComplaintCreate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { title: string; description: string }) => complaintsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['complaints'] }),
  })
}

export function useComplaintTraineeReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      action,
      correction_message,
    }: {
      id: number
      action: 'approve' | 'return_correction'
      correction_message?: string
    }) => complaintsApi.traineeReview(id, action, correction_message),
    onSuccess: (_, v) => {
      qc.invalidateQueries({ queryKey: ['complaints'] })
      qc.invalidateQueries({ queryKey: ['complaint', v.id] })
    },
  })
}

export function useComplaintOfficerReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'approve' | 'send_back' }) =>
      complaintsApi.officerReview(id, action),
    onSuccess: (_, v) => {
      qc.invalidateQueries({ queryKey: ['complaints'] })
      qc.invalidateQueries({ queryKey: ['complaint', v.id] })
    },
  })
}
