import { useQuery } from '@tanstack/react-query'
import { fetchPositions } from '@/api'

export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: fetchPositions,
    staleTime: 10 * 60 * 1000, // 10分
    retry: false,
  })
}
