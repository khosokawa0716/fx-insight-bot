import { apiClient } from '../lib/client'
import type { SignalItem, SignalListResponse } from '../types'

export async function fetchSignals(limit: number = 50): Promise<SignalItem[]> {
  const response = await apiClient.fetch<SignalListResponse>(`/api/v1/signals?limit=${limit}`)
  if (response.status !== 'success') {
    throw new Error('Failed to fetch signals')
  }
  return response.signals || []
}
