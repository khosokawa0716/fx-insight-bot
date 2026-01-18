import { useQuery } from '@tanstack/react-query'
import { fetchSignals } from '@/api'

export function useSignals(limit: number = 50) {
  return useQuery({
    queryKey: ['signals', limit],
    queryFn: () => fetchSignals(limit),
    staleTime: 1000 * 60 * 5, // 5分間キャッシュ
  })
}
