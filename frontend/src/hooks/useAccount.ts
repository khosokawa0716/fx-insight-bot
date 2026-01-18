import { useQuery } from '@tanstack/react-query'
import { fetchAccount } from '@/api'

const POLLING_INTERVAL = 30 * 1000 // 30秒

export function useAccount() {
  return useQuery({
    queryKey: ['account'],
    queryFn: fetchAccount,
    refetchInterval: POLLING_INTERVAL,
    refetchIntervalInBackground: false, // タブが非アクティブ時はポーリング停止
  })
}
