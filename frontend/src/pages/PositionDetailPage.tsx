import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, TrendingUp, TrendingDown, Clock, DollarSign } from 'lucide-react'
import { usePositions } from '../hooks'
import { formatCurrency } from '../lib/format'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Header, Footer } from '@/components/layout'
import { cn } from '@/lib/utils'

export function PositionDetailPage() {
  const { positionId } = useParams<{ positionId: string }>()
  const navigate = useNavigate()
  const { data: positions = [], isLoading, error } = usePositions()

  const position = positions.find(p => p.positionId === positionId)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent mx-auto" />
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error.message}</p>
          <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
        </div>
      </div>
    )
  }

  if (!position) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-4">Position not found</p>
          <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
        </div>
      </div>
    )
  }

  const profitLoss = parseFloat(position.lossGain)
  const isProfit = profitLoss >= 0

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Position Overview */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "p-2 rounded-lg",
                  position.side === 'BUY' ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900'
                )}>
                  {position.side === 'BUY' ? (
                    <TrendingUp className={cn("h-6 w-6", 'text-green-600 dark:text-green-400')} />
                  ) : (
                    <TrendingDown className={cn("h-6 w-6", 'text-red-600 dark:text-red-400')} />
                  )}
                </div>
                <div>
                  <CardTitle className="text-2xl">{position.symbol}</CardTitle>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Position ID: {position.positionId}
                  </p>
                </div>
              </div>
              <span
                className={cn(
                  "px-3 py-1 rounded-full text-sm font-medium",
                  position.side === 'BUY'
                    ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300'
                    : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-300'
                )}
              >
                {position.side}
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* P/L Card */}
              <div className={cn(
                "p-4 rounded-lg",
                isProfit ? 'bg-green-50 dark:bg-green-900/30' : 'bg-red-50 dark:bg-red-900/30'
              )}>
                <div className="flex items-center gap-2 mb-2">
                  <DollarSign className={cn(
                    "h-5 w-5",
                    isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  )} />
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Unrealized P/L
                  </span>
                </div>
                <div className={cn(
                  "text-3xl font-bold",
                  isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                )}>
                  {isProfit ? '+' : ''}{formatCurrency(position.lossGain)}
                </div>
              </div>

              {/* Position Details */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Size</span>
                  <span className="font-medium">{position.size} lots</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Entry Price</span>
                  <span className="font-medium">{position.price}</span>
                </div>
                {position.timestamp && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      Opened At
                    </span>
                    <span className="font-medium text-sm">
                      {new Date(position.timestamp).toLocaleString('ja-JP')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Position Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Position Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b dark:border-gray-700">
                <span className="text-gray-500 dark:text-gray-400">Symbol</span>
                <span className="font-medium">{position.symbol}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b dark:border-gray-700">
                <span className="text-gray-500 dark:text-gray-400">Direction</span>
                <span className={cn(
                  "font-medium",
                  position.side === 'BUY' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                )}>
                  {position.side === 'BUY' ? 'Long (Buy)' : 'Short (Sell)'}
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b dark:border-gray-700">
                <span className="text-gray-500 dark:text-gray-400">Quantity</span>
                <span className="font-medium">{position.size}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b dark:border-gray-700">
                <span className="text-gray-500 dark:text-gray-400">Entry Price</span>
                <span className="font-medium">{position.price}</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-gray-500 dark:text-gray-400">Current P/L</span>
                <span className={cn(
                  "font-bold",
                  isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                )}>
                  {formatCurrency(position.lossGain)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Back Button */}
        <div className="text-center">
          <Link to="/">
            <Button variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  )
}
