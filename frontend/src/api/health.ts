import { apiClient } from '../lib/client'
import type { HealthStatus } from '../types'

export async function fetchHealth(): Promise<HealthStatus> {
  return apiClient.fetch<HealthStatus>('/health')
}
