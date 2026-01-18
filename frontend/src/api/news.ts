import { apiClient } from '../lib/client'
import type { NewsItem, NewsListResponse } from '../types'

export async function fetchNews(limit: number = 20): Promise<NewsItem[]> {
  const response = await apiClient.fetch<NewsListResponse>(`/api/v1/news?limit=${limit}`)
  if (response.status !== 'success') {
    throw new Error('Failed to fetch news')
  }
  return response.news || []
}
