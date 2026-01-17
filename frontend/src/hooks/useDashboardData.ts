import { useState, useEffect, useCallback } from 'react'
import { fetchAccount, fetchPositions, fetchHealth } from '../api'
import type { AccountData, Position, HealthStatus } from '../types'

interface DashboardData {
  account: AccountData | null
  positions: Position[]
  health: HealthStatus | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useDashboardData(): DashboardData {
  const [account, setAccount] = useState<AccountData | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const [accountData, positionsData, healthData] = await Promise.all([
        fetchAccount(),
        fetchPositions(),
        fetchHealth(),
      ])

      setAccount(accountData)
      setPositions(positionsData)
      setHealth(healthData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    account,
    positions,
    health,
    loading,
    error,
    refetch: fetchData,
  }
}
