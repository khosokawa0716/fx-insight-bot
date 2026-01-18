import { useQueryClient } from '@tanstack/react-query'
import { Wallet, Activity, TrendingUp, AlertTriangle, RefreshCw } from 'lucide-react'
import { useAccount, usePositions, useHealth } from '../hooks'
import { formatCurrency } from '../lib/format'
import { useAuth } from '../contexts/AuthContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function DashboardPage() {
  const queryClient = useQueryClient()
  const { data: account, isLoading: accountLoading, error: accountError } = useAccount()
  const { data: positions = [], isLoading: positionsLoading, error: positionsError } = usePositions()
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth()
  const { user, signOut } = useAuth()

  const loading = accountLoading || positionsLoading || healthLoading
  const error = accountError || positionsError || healthError

  const refetch = () => {
    queryClient.invalidateQueries({ queryKey: ['account'] })
    queryClient.invalidateQueries({ queryKey: ['positions'] })
    queryClient.invalidateQueries({ queryKey: ['health'] })
  }

  // 証拠金維持率を計算
  const marginRatio = account?.margin && account?.equity
    ? (parseFloat(account.equity) / parseFloat(account.margin)) * 100
    : null

  // リスクレベルを判定
  const getRiskLevel = (ratio: number | null) => {
    if (ratio === null) return { level: 'unknown', color: 'text-gray-500', bgColor: 'bg-gray-100' }
    if (ratio >= 300) return { level: 'Safe', color: 'text-green-600', bgColor: 'bg-green-100' }
    if (ratio >= 150) return { level: 'Normal', color: 'text-yellow-600', bgColor: 'bg-yellow-100' }
    return { level: 'Warning', color: 'text-red-600', bgColor: 'bg-red-100' }
  }

  const riskStatus = getRiskLevel(marginRatio)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">
            FX Insight Bot
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={signOut}>
              Sign out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center justify-between">
            <span>{error.message}</span>
            <Button variant="outline" size="sm" onClick={refetch}>
              Retry
            </Button>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-500" />
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Balance Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    Total Balance
                  </CardTitle>
                  <Wallet className="h-4 w-4 text-gray-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(account?.balance)}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Available: {formatCurrency(account?.availableAmount)}
                  </p>
                </CardContent>
              </Card>

              {/* Equity Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    Equity
                  </CardTitle>
                  <TrendingUp className="h-4 w-4 text-gray-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(account?.equity)}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Margin: {formatCurrency(account?.margin)}
                  </p>
                </CardContent>
              </Card>

              {/* P/L Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    Unrealized P/L
                  </CardTitle>
                  <Activity className="h-4 w-4 text-gray-400" />
                </CardHeader>
                <CardContent>
                  <div className={cn(
                    "text-2xl font-bold",
                    account?.profitLoss && parseFloat(account.profitLoss) >= 0
                      ? 'text-green-600'
                      : 'text-red-600'
                  )}>
                    {formatCurrency(account?.profitLoss)}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {positions.length} position(s)
                  </p>
                </CardContent>
              </Card>

              {/* Risk Status Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    Margin Ratio
                  </CardTitle>
                  <AlertTriangle className={cn("h-4 w-4", riskStatus.color)} />
                </CardHeader>
                <CardContent>
                  <div className={cn("text-2xl font-bold", riskStatus.color)}>
                    {marginRatio !== null ? `${marginRatio.toFixed(1)}%` : '-'}
                  </div>
                  <p className={cn("text-xs mt-1 px-2 py-0.5 rounded-full inline-block", riskStatus.bgColor, riskStatus.color)}>
                    {riskStatus.level}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* System Status */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">System Status</CardTitle>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "w-2 h-2 rounded-full",
                        health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                      )}
                    />
                    <span className="text-sm text-gray-600">
                      {health?.status === 'healthy' ? 'Online' : 'Offline'}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Auto-refresh every 30 seconds</span>
                  <Button variant="outline" size="sm" onClick={refetch} disabled={loading}>
                    <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                    Refresh Now
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Positions Table */}
            <Card>
              <CardHeader>
                <CardTitle>Open Positions</CardTitle>
              </CardHeader>
              <CardContent>
                {positions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No open positions
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Symbol
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Side
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Size
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Entry Price
                          </th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            P/L
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {positions.map((position) => (
                          <tr key={position.positionId} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm font-medium text-gray-900">
                              {position.symbol}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <span
                                className={cn(
                                  "px-2 py-1 rounded text-xs font-medium",
                                  position.side === 'BUY'
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-red-100 text-red-800'
                                )}
                              >
                                {position.side}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {position.size}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {position.price}
                            </td>
                            <td
                              className={cn(
                                "px-4 py-3 text-sm font-medium text-right",
                                parseFloat(position.lossGain) >= 0
                                  ? 'text-green-600'
                                  : 'text-red-600'
                              )}
                            >
                              {formatCurrency(position.lossGain)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t mt-auto bg-white">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          FX Insight Bot - Display Only Dashboard
        </div>
      </footer>
    </div>
  )
}
