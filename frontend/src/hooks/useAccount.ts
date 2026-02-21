import { useQuery } from '@tanstack/react-query'
import { fetchAccount } from '@/api'

const POLLING_INTERVAL = 30 * 1000 // 30秒

export function useAccount() {
  return useQuery({
    queryKey: ['account'],
    queryFn: fetchAccount,
    refetchInterval: (query) => query.state.status === 'error' ? false : POLLING_INTERVAL,
    refetchIntervalInBackground: false,
    retry: false,
  })
}
