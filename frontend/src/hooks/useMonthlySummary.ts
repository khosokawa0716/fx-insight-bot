import { useQuery } from '@tanstack/react-query'
import { fetchMonthlySummary } from '@/api/trade'

export function useMonthlySummary() {
  return useQuery({
    queryKey: ['monthlySummary'],
    queryFn: fetchMonthlySummary,
    staleTime: 5 * 60 * 1000, // 5分
    retry: false,
  })
}
