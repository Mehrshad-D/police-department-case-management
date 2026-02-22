import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { evidenceApi, evidenceLinksApi } from '@/api/endpoints'

export function useEvidenceList(caseId?: number | null) {
  return useQuery({
    queryKey: ['evidence', caseId],
    queryFn: () => evidenceApi.list(caseId ? { case: caseId } : undefined),
    enabled: true,
  })
}

export function useEvidence(id: number | null) {
  return useQuery({
    queryKey: ['evidence', id],
    queryFn: () => evidenceApi.get(id!),
    enabled: id != null,
  })
}

export function useEvidenceCreate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: FormData | Record<string, unknown>) => evidenceApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['evidence'] }),
  })
}

export function useEvidenceLinks(caseId: number | null) {
  return useQuery({
    queryKey: ['evidence-links', caseId],
    queryFn: () => evidenceLinksApi.list(caseId!),
    enabled: caseId != null,
  })
}

export function useEvidenceLinkCreate(caseId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { evidence_from: number; evidence_to: number; link_type?: string }) =>
      evidenceLinksApi.create(caseId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['evidence-links', caseId] }),
  })
}

export function useEvidenceLinkDelete(caseId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (linkId: number) => evidenceLinksApi.delete(caseId, linkId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['evidence-links', caseId] }),
  })
}
