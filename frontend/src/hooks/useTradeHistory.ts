import { useQuery } from '@tanstack/react-query'
import { fetchTradeHistory } from '@/api/trade'

export function useTradeHistory(limit = 50) {
  return useQuery({
    queryKey: ['tradeHistory', limit],
    queryFn: () => fetchTradeHistory(limit),
    staleTime: 60 * 1000, // 1分
    retry: false,
  })
}
