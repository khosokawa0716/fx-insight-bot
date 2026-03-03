import { Link } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Wallet, Activity, TrendingUp, AlertTriangle, RefreshCw, ChevronRight, History, BarChart2 } from 'lucide-react'
import { useAccount, usePositions, useHealth, useTradeHistory, useMonthlySummary } from '../hooks'
import { formatCurrency } from '../lib/format'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Header, Footer } from '@/components/layout'
import { cn } from '@/lib/utils'
import type { TradeHistoryItem } from '@/types'

function actionBadge(item: TradeHistoryItem) {
  if (item.side === 'HOLD') {
    return <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300">HOLD</span>
  }
  if (item.skip_reason) {
    return <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">SKIP</span>
  }
  if (item.side === 'BUY') {
    return <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300">BUY</span>
  }
  return <span className="px-2 py-1 rounded text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-300">SELL</span>
}

function pnlCell(pnl: number | null | undefined) {
  if (pnl == null) return <span className="text-gray-400">-</span>
  return (
    <span className={pnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
      {pnl >= 0 ? '+' : ''}{pnl.toFixed(0)}円
    </span>
  )
}

export function DashboardPage() {
  const queryClient = useQueryClient()
  const { data: account, isLoading: accountLoading, error: accountError } = useAccount()
  const { data: positions = [], isLoading: positionsLoading, error: positionsError } = usePositions()
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth()
  const { data: tradeHistory = [], isLoading: historyLoading } = useTradeHistory(30)
  const { data: monthly } = useMonthlySummary()

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

            {/* Monthly Summary */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <BarChart2 className="h-4 w-4" />
                  Monthly Summary
                  {monthly && (
                    <span className="text-xs font-normal text-gray-400">（{monthly.period}）</span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!monthly ? (
                  <div className="text-center py-4 text-gray-400 text-sm">Loading...</div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">取引数</p>
                      <p className="text-xl font-bold">{monthly.data.total_trades}</p>
                      <p className="text-xs text-gray-400">
                        勝{monthly.data.win_count} / 負{monthly.data.loss_count}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">勝率</p>
                      <p className={cn(
                        "text-xl font-bold",
                        monthly.data.win_rate >= 50
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      )}>
                        {monthly.data.win_rate.toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-400">SKIP {monthly.data.skip_count}件</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">実損益</p>
                      <p className={cn(
                        "text-xl font-bold",
                        monthly.data.actual_pnl >= 0
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      )}>
                        {monthly.data.actual_pnl >= 0 ? '+' : ''}{monthly.data.actual_pnl.toFixed(0)}円
                      </p>
                      <p className="text-xs text-gray-400">
                        baseline {monthly.data.baseline_pnl >= 0 ? '+' : ''}{monthly.data.baseline_pnl.toFixed(0)}円
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">AI優位性</p>
                      <p className={cn(
                        "text-xl font-bold",
                        monthly.data.ai_advantage >= 0
                          ? 'text-blue-600 dark:text-blue-400'
                          : 'text-orange-600 dark:text-orange-400'
                      )}>
                        {monthly.data.ai_advantage >= 0 ? '+' : ''}{monthly.data.ai_advantage.toFixed(0)}円
                      </p>
                      <p className="text-xs text-gray-400">actual − baseline</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

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

            {/* Trade History Table */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <CardTitle className="flex items-center gap-2">
                  <History className="h-4 w-4" />
                  Trade History
                  <span className="text-xs font-normal text-gray-400">（直近30件）</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {historyLoading ? (
                  <div className="text-center py-8 text-gray-400">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-1" />
                    Loading...
                  </div>
                ) : tradeHistory.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No trade history
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full">
                      <thead>
                        <tr className="border-b dark:border-gray-700">
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Date</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Symbol</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Action</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Lot</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Entry</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">P/L</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                        {tradeHistory.map((item) => (
                          <tr key={item.trade_id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                            <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                              {new Date(item.created_at).toLocaleString('ja-JP', {
                                month: '2-digit', day: '2-digit',
                                hour: '2-digit', minute: '2-digit',
                              })}
                            </td>
                            <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
                              {item.symbol.replace('_', '/')}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {actionBadge(item)}
                            </td>
                            <td className="px-4 py-3 text-sm text-right text-gray-600 dark:text-gray-400">
                              {item.used_lot > 0 ? item.used_lot.toLocaleString() : '-'}
                            </td>
                            <td className="px-4 py-3 text-sm text-right text-gray-600 dark:text-gray-400">
                              {item.entry_price != null ? item.entry_price.toFixed(3) : '-'}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                              {item.status ?? '-'}
                            </td>
                            <td className="px-4 py-3 text-sm text-right">
                              {pnlCell(item.actual_pnl)}
                            </td>
                            <td className="px-4 py-3 text-xs text-gray-400 dark:text-gray-500 max-w-[200px] truncate" title={item.reason}>
                              {item.reason || '-'}
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
