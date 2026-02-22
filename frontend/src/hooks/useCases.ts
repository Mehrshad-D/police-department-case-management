import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { casesApi } from '@/api/endpoints'
import type { Case } from '@/types'

export function useCasesList(params?: { status?: string; severity?: string }) {
  return useQuery({
    queryKey: ['cases', params],
    queryFn: () => casesApi.list(params),
  })
}

export function useCase(id: number | null) {
  return useQuery({
    queryKey: ['case', id],
    queryFn: () => casesApi.get(id!),
    enabled: id != null,
  })
}

export function useCaseCreate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Case>) => casesApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cases'] }),
  })
}

export function useCaseUpdate(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Case>) => casesApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cases'] })
      qc.invalidateQueries({ queryKey: ['case', id] })
    },
  })
}
