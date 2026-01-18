import { useQuery } from '@tanstack/react-query'
import { fetchNews } from '@/api'

export function useNews(limit: number = 20) {
  return useQuery({
    queryKey: ['news', limit],
    queryFn: () => fetchNews(limit),
    staleTime: 1000 * 60 * 5, // 5分間キャッシュ
  })
}
