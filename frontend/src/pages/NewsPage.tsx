import { Link } from 'react-router-dom'
import { ArrowLeft, ExternalLink, TrendingUp, TrendingDown, Minus, Clock, RefreshCw } from 'lucide-react'
import { useNews } from '../hooks'
import { useAuth } from '../contexts/AuthContext'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { NewsItem } from '../types'

function getSentimentInfo(sentiment: number) {
  if (sentiment >= 1) return { label: 'Bullish', color: 'text-green-600', bgColor: 'bg-green-100', icon: TrendingUp }
  if (sentiment <= -1) return { label: 'Bearish', color: 'text-red-600', bgColor: 'bg-red-100', icon: TrendingDown }
  return { label: 'Neutral', color: 'text-gray-600', bgColor: 'bg-gray-100', icon: Minus }
}

function getSignalInfo(signal: string) {
  switch (signal) {
    case 'BUY_CANDIDATE':
      return { label: 'BUY', color: 'text-green-700', bgColor: 'bg-green-100' }
    case 'SELL_CANDIDATE':
      return { label: 'SELL', color: 'text-red-700', bgColor: 'bg-red-100' }
    case 'RISK_OFF':
      return { label: 'RISK OFF', color: 'text-orange-700', bgColor: 'bg-orange-100' }
    default:
      return { label: 'IGNORE', color: 'text-gray-500', bgColor: 'bg-gray-100' }
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

function NewsCard({ news }: { news: NewsItem }) {
  const sentimentInfo = getSentimentInfo(news.sentiment)
  const signalInfo = getSignalInfo(news.signal)
  const SentimentIcon = sentimentInfo.icon

  const publishedDate = new Date(news.published_at)

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            {/* Title */}
            <h3 className="font-medium text-gray-900 mb-2 line-clamp-2">
              {news.title}
            </h3>

            {/* Summary */}
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {news.summary}
            </p>

            {/* Meta */}
            <div className="flex flex-wrap items-center gap-3 text-xs">
              {/* Sentiment */}
              <span className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full",
                sentimentInfo.bgColor,
                sentimentInfo.color
              )}>
                <SentimentIcon className="h-3 w-3" />
                {sentimentInfo.label}
              </span>

              {/* Signal */}
              <span className={cn(
                "px-2 py-0.5 rounded-full font-medium",
                signalInfo.bgColor,
                signalInfo.color
              )}>
                {signalInfo.label}
              </span>

              {/* Time Horizon */}
              <span className="text-gray-500">
                {getTimeHorizonLabel(news.time_horizon)}
              </span>

              {/* Date */}
              <span className="text-gray-400 flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {publishedDate.toLocaleDateString('ja-JP')}
              </span>
            </div>

            {/* Impact */}
            <div className="flex gap-4 mt-3">
              <ImpactBars value={news.impact_usdjpy} label="USD/JPY" />
              <ImpactBars value={news.impact_eurjpy} label="EUR/JPY" />
            </div>
          </div>

          {/* Link */}
          <a
            href={news.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-blue-500 transition-colors"
          >
            <ExternalLink className="h-5 w-5" />
          </a>
        </div>
      </CardContent>
    </Card>
  )
}

export function NewsPage() {
  const { data: news = [], isLoading, error, refetch } = useNews(30)
  const { user, signOut } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <h1 className="text-xl font-bold text-gray-900">
              News
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={signOut}>
              Sign out
            </Button>
          </div>
        </div>
      </header>

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
            <p className="mt-2 text-gray-600">Loading news...</p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <p className="text-sm text-gray-500">
                {news.length} articles
              </p>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>

            {/* News List */}
            {news.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-gray-500">
                  No news available
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {news.map((item) => (
                  <NewsCard key={item.news_id} news={item} />
                ))}
              </div>
            )}
          </>
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
