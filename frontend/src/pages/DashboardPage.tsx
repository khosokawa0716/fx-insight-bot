import { Link } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Wallet, Activity, TrendingUp, AlertTriangle, RefreshCw, ChevronRight } from 'lucide-react'
import { useAccount, usePositions, useHealth } from '../hooks'
import { formatCurrency } from '../lib/format'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Header, Footer } from '@/components/layout'
import { cn } from '@/lib/utils'

export function DashboardPage() {
  const queryClient = useQueryClient()
  const { data: account, isLoading: accountLoading, error: accountError } = useAccount()
  const { data: positions = [], isLoading: positionsLoading, error: positionsError } = usePositions()
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth()

  const loading = accountLoading || positionsLoading || healthLoading
  const error = accountError || positionsError || healthError
  const isMaintenance = error?.message === 'MAINTENANCE'

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
    if (ratio === null) return { level: 'unknown', color: 'text-gray-500 dark:text-gray-400', bgColor: 'bg-gray-100 dark:bg-gray-800' }
    if (ratio >= 300) return { level: 'Safe', color: 'text-green-600 dark:text-green-400', bgColor: 'bg-green-100 dark:bg-green-900' }
    if (ratio >= 150) return { level: 'Normal', color: 'text-yellow-600 dark:text-yellow-400', bgColor: 'bg-yellow-100 dark:bg-yellow-900' }
    return { level: 'Warning', color: 'text-red-600 dark:text-red-400', bgColor: 'bg-red-100 dark:bg-red-900' }
  }

  const riskStatus = getRiskLevel(marginRatio)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className={cn(
            "mb-6 p-4 border rounded-lg flex items-center justify-between",
            isMaintenance
              ? "bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-800 text-yellow-700 dark:text-yellow-400"
              : "bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400"
          )}>
            <span>
              {isMaintenance
                ? 'GMOコイン メンテナンス中です。終了後に自動で再接続されません。Retryボタンで更新してください。'
                : error.message}
            </span>
            <Button variant="outline" size="sm" onClick={refetch}>
              Retry
            </Button>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-500" />
            <p className="mt-2 text-gray-600 dark:text-gray-400">Loading...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Balance Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Total Balance
                  </CardTitle>
                  <Wallet className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(account?.balance)}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Available: {formatCurrency(account?.availableAmount)}
                  </p>
                </CardContent>
              </Card>

              {/* Equity Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Equity
                  </CardTitle>
                  <TrendingUp className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(account?.equity)}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Margin: {formatCurrency(account?.margin)}
                  </p>
                </CardContent>
              </Card>

              {/* P/L Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Unrealized P/L
                  </CardTitle>
                  <Activity className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                </CardHeader>
                <CardContent>
                  <div className={cn(
                    "text-2xl font-bold",
                    account?.profitLoss && parseFloat(account.profitLoss) >= 0
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  )}>
                    {formatCurrency(account?.profitLoss)}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {positions.length} position(s)
                  </p>
                </CardContent>
              </Card>

              {/* Risk Status Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400">
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
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {health?.status === 'healthy' ? 'Online' : 'Offline'}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Auto-refresh every 30 seconds</span>
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
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No open positions
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full">
                      <thead>
                        <tr className="border-b dark:border-gray-700">
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Symbol
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Side
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Size
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Entry Price
                          </th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            P/L
                          </th>
                          <th className="px-4 py-3 w-8"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                        {positions.map((position) => (
                          <tr key={position.positionId} className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer group">
                            <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
                              <Link to={`/position/${position.positionId}`} className="hover:text-blue-600 dark:hover:text-blue-400">
                                {position.symbol}
                              </Link>
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <span
                                className={cn(
                                  "px-2 py-1 rounded text-xs font-medium",
                                  position.side === 'BUY'
                                    ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300'
                                    : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-300'
                                )}
                              >
                                {position.side}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                              {position.size}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                              {position.price}
                            </td>
                            <td
                              className={cn(
                                "px-4 py-3 text-sm font-medium text-right",
                                parseFloat(position.lossGain) >= 0
                                  ? 'text-green-600 dark:text-green-400'
                                  : 'text-red-600 dark:text-red-400'
                              )}
                            >
                              {formatCurrency(position.lossGain)}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-400 dark:text-gray-500">
                              <Link to={`/position/${position.positionId}`}>
                                <ChevronRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                              </Link>
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

      <Footer />
    </div>
  )
}
