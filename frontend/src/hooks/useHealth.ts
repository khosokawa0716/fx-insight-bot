import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '@/api'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    staleTime: 10 * 60 * 1000, // 10分
  })
}
