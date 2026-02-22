import { useQuery } from '@tanstack/react-query'
import { statisticsApi } from '@/api/endpoints'

export function useStatistics() {
  return useQuery({
    queryKey: ['statistics'],
    queryFn: () => statisticsApi.get(),
  })
}
