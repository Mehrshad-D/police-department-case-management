import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { suspectsApi } from '@/api/endpoints'

export function useSuspectsList(params?: { case?: number }) {
  return useQuery({
    queryKey: ['suspects', params],
    queryFn: () => suspectsApi.list(params),
  })
}

export function useSuspectsHighPriority() {
  return useQuery({
    queryKey: ['suspects', 'high-priority'],
    queryFn: () => suspectsApi.highPriority(),
  })
}

export function useSuspect(id: number | null) {
  return useQuery({
    queryKey: ['suspect', id],
    queryFn: () => suspectsApi.get(id!),
    enabled: id != null,
  })
}

export function useSuspectPropose() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ caseId, userId }: { caseId: number; userId: number }) =>
      suspectsApi.propose(caseId, userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['suspects'] }),
  })
}

export function useSuspectSupervisorReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'approve' | 'reject' }) =>
      suspectsApi.supervisorReview(id, action),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['suspects'] }),
  })
}
