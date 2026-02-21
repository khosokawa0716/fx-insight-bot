import { useQuery } from '@tanstack/react-query'
import { fetchPositions } from '@/api'

const POLLING_INTERVAL = 30 * 1000 // 30秒

export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: fetchPositions,
    refetchInterval: (query) => query.state.status === 'error' ? false : POLLING_INTERVAL,
    refetchIntervalInBackground: false,
    retry: false,
  })
}
