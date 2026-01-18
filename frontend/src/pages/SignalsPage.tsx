import { TrendingUp, TrendingDown, AlertTriangle, Clock, RefreshCw } from 'lucide-react'
import { useSignals } from '../hooks'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Header, Footer } from '@/components/layout'
import { cn } from '@/lib/utils'
import type { SignalItem } from '../types'

function getSignalInfo(signal: string) {
  switch (signal) {
    case 'BUY_CANDIDATE':
      return {
        label: 'BUY',
        color: 'text-green-700',
        bgColor: 'bg-green-100',
        borderColor: 'border-l-green-500',
        icon: TrendingUp
      }
    case 'SELL_CANDIDATE':
      return {
        label: 'SELL',
        color: 'text-red-700',
        bgColor: 'bg-red-100',
        borderColor: 'border-l-red-500',
        icon: TrendingDown
      }
    case 'RISK_OFF':
      return {
        label: 'RISK OFF',
        color: 'text-orange-700',
        bgColor: 'bg-orange-100',
        borderColor: 'border-l-orange-500',
        icon: AlertTriangle
      }
    default:
      return {
        label: signal,
        color: 'text-gray-500',
        bgColor: 'bg-gray-100',
        borderColor: 'border-l-gray-300',
        icon: Clock
      }
  }
}

function getTimeHorizonLabel(horizon: string) {
  switch (horizon) {
    case 'immediate': return 'Immediate'
    case 'short-term': return 'Short-term'
    case 'medium-term': return 'Medium-term'
    case 'long-term': return 'Long-term'
    default: return horizon
  }
}

function ImpactBars({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-16">{label}</span>
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={cn(
              "w-2 h-3 rounded-sm",
              i <= value ? 'bg-blue-500' : 'bg-gray-200'
            )}
          />
        ))}
      </div>
    </div>
  )
}

function SignalCard({ signal }: { signal: SignalItem }) {
  const signalInfo = getSignalInfo(signal.signal)
  const SignalIcon = signalInfo.icon

  const publishedDate = new Date(signal.published_at)

  return (
    <Card className={cn("border-l-4", signalInfo.borderColor)}>
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Signal Icon */}
          <div className={cn(
            "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center",
            signalInfo.bgColor
          )}>
            <SignalIcon className={cn("h-5 w-5", signalInfo.color)} />
          </div>

          <div className="flex-1 min-w-0">
            {/* Signal Type & Time */}
            <div className="flex items-center gap-2 mb-1">
              <span className={cn(
                "px-2 py-0.5 rounded-full text-xs font-bold",
                signalInfo.bgColor,
                signalInfo.color
              )}>
                {signalInfo.label}
              </span>
              <span className="text-xs text-gray-400 flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {publishedDate.toLocaleDateString('ja-JP')} {publishedDate.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>

            {/* Title */}
            <h3 className="font-medium text-gray-900 mb-1 line-clamp-2">
              {signal.title}
            </h3>

            {/* Summary */}
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {signal.summary}
            </p>

            {/* Meta */}
            <div className="flex flex-wrap items-center gap-4">
              {/* Time Horizon */}
              <span className="text-xs text-gray-500">
                {getTimeHorizonLabel(signal.time_horizon)}
              </span>

              {/* Sentiment */}
              <span className={cn(
                "text-xs",
                signal.sentiment >= 1 ? 'text-green-600' :
                signal.sentiment <= -1 ? 'text-red-600' : 'text-gray-500'
              )}>
                Sentiment: {signal.sentiment > 0 ? '+' : ''}{signal.sentiment}
              </span>

              {/* Impact */}
              <ImpactBars value={signal.impact_usdjpy} label="USD/JPY" />
              <ImpactBars value={signal.impact_eurjpy} label="EUR/JPY" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function SignalsPage() {
  const { data: signals = [], isLoading, error, refetch } = useSignals(50)

  // Group signals by date
  const groupedSignals = signals.reduce((groups, signal) => {
    const date = new Date(signal.published_at).toLocaleDateString('ja-JP')
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(signal)
    return groups
  }, {} as Record<string, SignalItem[]>)

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center justify-between">
            <span>{error.message}</span>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        )}

        {isLoading ? (
          <div className="text-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-500" />
            <p className="mt-2 text-gray-600">Loading signals...</p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <p className="text-sm text-gray-500">
                {signals.length} signals (BUY / SELL / RISK OFF)
              </p>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>

            {/* Signals List */}
            {signals.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-gray-500">
                  No signals available
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-6">
                {Object.entries(groupedSignals).map(([date, dateSignals]) => (
                  <div key={date}>
                    <h2 className="text-sm font-medium text-gray-500 mb-3">
                      {date}
                    </h2>
                    <div className="space-y-3">
                      {dateSignals.map((signal) => (
                        <SignalCard key={signal.news_id} signal={signal} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>

      <Footer />
    </div>
  )
}
