import { useQuery } from '@tanstack/react-query'
import { fetchTradeHistory } from '@/api/trade'

export function useTradeHistory(limit = 50, excludeHold = false) {
  return useQuery({
    queryKey: ['tradeHistory', limit, excludeHold],
    queryFn: () => fetchTradeHistory(limit, excludeHold),
    staleTime: 60 * 1000, // 1分
    retry: false,
  })
}
