import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '@/api'

const POLLING_INTERVAL = 30 * 1000 // 30秒

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: POLLING_INTERVAL,
    refetchIntervalInBackground: false,
  })
}
