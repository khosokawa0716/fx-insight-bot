import { apiClient } from '../lib/client'
import type { AccountData, Position, ApiResponse, PositionsResponse, TradeHistoryItem, TradeHistoryResponse, MonthlySummaryResponse } from '../types'

export async function fetchAccount(): Promise<AccountData> {
  const response = await apiClient.fetch<ApiResponse<AccountData>>('/api/v1/trade/account')
  if (response.status !== 'success' || !response.data) {
    throw new Error('Failed to fetch account data')
  }
  return response.data
}

export async function fetchPositions(): Promise<Position[]> {
  const response = await apiClient.fetch<PositionsResponse>('/api/v1/trade/positions')
  if (response.status !== 'success') {
    throw new Error('Failed to fetch positions')
  }
  return response.positions || []
}

export async function fetchMonthlySummary(): Promise<MonthlySummaryResponse> {
  const response = await apiClient.fetch<MonthlySummaryResponse>('/api/v1/trade/monthly-summary')
  if (response.status !== 'success') {
    throw new Error('Failed to fetch monthly summary')
  }
  return response
}

export async function fetchTradeHistory(limit = 50): Promise<TradeHistoryItem[]> {
  const response = await apiClient.fetch<TradeHistoryResponse>(
    `/api/v1/trade/history?limit=${limit}`
  )
  if (response.status !== 'success') {
    throw new Error('Failed to fetch trade history')
  }
  return response.items || []
}
