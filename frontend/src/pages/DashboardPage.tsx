import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import {
  Wallet, Activity, RefreshCw,
  ChevronRight, ChevronDown, BarChart2, Newspaper, History,
} from 'lucide-react'
import { useAccount, usePositions, useHealth, useTradeHistory, useMonthlySummary, useNews } from '../hooks'
import { formatCurrency } from '../lib/format'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Header, Footer } from '@/components/layout'
import { cn } from '@/lib/utils'
import type { TradeHistoryItem, NewsItem } from '@/types'

// ─── ユーティリティ ────────────────────────────────────────────────────────────

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

function pnlText(pnl: number | null | undefined) {
  if (pnl == null) return <span className="text-gray-400">-</span>
  return (
    <span className={pnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
      {pnl >= 0 ? '+' : ''}{pnl.toFixed(0)}円
    </span>
  )
}

function sentimentBar(value: number | null | undefined) {
  if (value == null) return <span className="text-gray-400">-</span>
  const clamped = Math.max(-2, Math.min(2, value))
  const pct = ((clamped + 2) / 4) * 100
  const color = value > 0 ? 'bg-green-500' : value < 0 ? 'bg-red-500' : 'bg-gray-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs tabular-nums w-8 text-right">{value > 0 ? '+' : ''}{value.toFixed(1)}</span>
    </div>
  )
}

function sentimentBadge(value: number | null | undefined) {
  if (value == null) return null
  if (value >= 1) return <span className="px-1.5 py-0.5 rounded text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300">強気</span>
  if (value <= -1) return <span className="px-1.5 py-0.5 rounded text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300">弱気</span>
  return <span className="px-1.5 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">中立</span>
}

function signalBadge(signal: NewsItem['signal']) {
  const map = {
    BUY_CANDIDATE: 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
    SELL_CANDIDATE: 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300',
    RISK_OFF: 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300',
    IGNORE: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
  }
  const label = {
    BUY_CANDIDATE: '買い候補',
    SELL_CANDIDATE: '売り候補',
    RISK_OFF: 'リスクオフ',
    IGNORE: '無視',
  }
  return <span className={cn('px-1.5 py-0.5 rounded text-xs font-medium', map[signal])}>{label[signal]}</span>
}

function impactDots(value: number) {
  return (
    <span className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={cn('w-1.5 h-1.5 rounded-full', i < value ? 'bg-blue-500' : 'bg-gray-200 dark:bg-gray-600')}
        />
      ))}
    </span>
  )
}

// reason 文字列を | で分割し、lot= で始まる重複部分を除去
function parseReasonPoints(reason: string): string[] {
  return reason
    .split(' | ')
    .map(s => s.trim())
    .filter(s => s.length > 0 && !s.startsWith('lot='))
}

// スコアバー（閾値付き）
const SCORE_THRESHOLD = 4

function ScoreBar({
  label,
  score,
  active,
  color,
}: {
  label: string
  score: number | null | undefined
  active: boolean
  color: 'green' | 'red'
}) {
  if (score == null) {
    return (
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-400">{label}</span>
          <span className="text-gray-400">-</span>
        </div>
        <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full" />
      </div>
    )
  }

  const pct = Math.min(score / SCORE_THRESHOLD, 1) * 100
  const barColor = active
    ? color === 'green' ? 'bg-green-500' : 'bg-red-500'
    : 'bg-gray-300 dark:bg-gray-600'
  const labelColor = active
    ? color === 'green' ? 'text-green-700 dark:text-green-400 font-semibold' : 'text-red-700 dark:text-red-400 font-semibold'
    : 'text-gray-500 dark:text-gray-400'

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className={labelColor}>{label}</span>
        <span className={labelColor}>
          {score}pt
          {active
            ? <span className="ml-1 font-bold">→ 発動</span>
            : <span className="ml-1 text-gray-400 font-normal">/ 閾値{SCORE_THRESHOLD}pt</span>
          }
        </span>
      </div>
      <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full transition-all', barColor)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

// ─── 直近判断ログカード ────────────────────────────────────────────────────────

function JudgmentCard({ item }: { item: TradeHistoryItem }) {
  const isSkip = !!item.skip_reason
  const isHold = item.side === 'HOLD'
  const isTrade = !isSkip && !isHold

  const borderColor = isHold
    ? 'border-l-yellow-400'
    : isSkip
    ? 'border-l-gray-300 dark:border-l-gray-600'
    : item.side === 'BUY'
    ? 'border-l-green-500'
    : 'border-l-red-500'

  return (
    <Card className={cn('border-l-4', borderColor)}>
      <CardContent className="pt-4 space-y-3">
        {/* ヘッダ行 */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-wrap">
            {actionBadge(item)}
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {item.symbol.replace('_', '/')}
            </span>
            {isTrade && item.used_lot > 0 && (
              <span className="text-xs text-gray-500 dark:text-gray-400">{item.used_lot.toLocaleString()}通貨</span>
            )}
          </div>
          <span className="text-xs text-gray-400 whitespace-nowrap">
            {new Date(item.created_at).toLocaleString('ja-JP', {
              month: '2-digit', day: '2-digit',
              hour: '2-digit', minute: '2-digit',
            })}
          </span>
        </div>

        {/* 判断根拠（箇条書き） */}
        {item.reason && (() => {
          const points = parseReasonPoints(item.reason)
          return points.length > 0 ? (
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">判断根拠</p>
              <ul className="space-y-1">
                {points.map((point, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-sm text-gray-800 dark:text-gray-200">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0" />
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          ) : null
        })()}
        {item.skip_reason && (
          <div>
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">スキップ理由</p>
            <p className="text-sm text-gray-800 dark:text-gray-200">{item.skip_reason}</p>
          </div>
        )}
        {item.lot_reason && (
          <div>
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">ロット根拠（AI）</p>
            <p className="text-sm text-gray-700 dark:text-gray-300">{item.lot_reason}</p>
          </div>
        )}

        {/* スコア行 */}
        <div className="pt-2 border-t dark:border-gray-700 space-y-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <ScoreBar
              label="買いスコア"
              score={item.buy_score}
              active={!isSkip && !isHold && item.side === 'BUY'}
              color="green"
            />
            <ScoreBar
              label="売りスコア"
              score={item.sell_score}
              active={!isSkip && !isHold && item.side === 'SELL'}
              color="red"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-gray-400 mb-0.5">確信度</p>
              <p className="text-sm font-medium">{item.confidence != null ? `${(item.confidence * 100).toFixed(0)}%` : '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">AIセンチメント</p>
              {sentimentBar(item.ai_sentiment)}
            </div>
          </div>
        </div>

        {/* 損益 */}
        {isTrade && (
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-400 text-xs">損益:</span>
            {pnlText(item.actual_pnl)}
            {item.baseline_pnl != null && (
              <span className="text-xs text-gray-400">
                baseline: {pnlText(item.baseline_pnl)}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ─── 取引履歴行（展開） ───────────────────────────────────────────────────────

function HistoryRow({ item }: { item: TradeHistoryItem }) {
  const [open, setOpen] = useState(false)
  const isSkip = !!item.skip_reason
  const isHold = item.side === 'HOLD'

  return (
    <>
      <tr
        className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
        onClick={() => setOpen(o => !o)}
      >
        <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
          {new Date(item.created_at).toLocaleString('ja-JP', {
            month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit',
          })}
        </td>
        <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
          {item.symbol.replace('_', '/')}
        </td>
        <td className="px-4 py-3 text-sm">{actionBadge(item)}</td>
        <td className="px-4 py-3 text-sm text-right text-gray-600 dark:text-gray-400">
          {item.used_lot > 0 ? item.used_lot.toLocaleString() : '-'}
        </td>
        <td className="px-4 py-3 text-sm text-right text-gray-600 dark:text-gray-400">
          {item.entry_price != null ? item.entry_price.toFixed(3) : '-'}
        </td>
        <td className="px-4 py-3 text-sm text-right">{pnlText(item.actual_pnl)}</td>
        <td className="px-4 py-3 text-sm text-gray-400">
          {open
            ? <ChevronDown className="h-4 w-4" />
            : <ChevronRight className="h-4 w-4" />
          }
        </td>
      </tr>
      {open && (
        <tr className="bg-gray-50 dark:bg-gray-800/60">
          <td colSpan={7} className="px-6 py-4">
            <div className="space-y-3 text-sm">
              {item.reason && (() => {
                const points = parseReasonPoints(item.reason)
                return points.length > 0 ? (
                  <div>
                    <span className="text-xs font-medium text-gray-400">判断根拠</span>
                    <ul className="mt-1 space-y-1">
                      {points.map((point, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-gray-700 dark:text-gray-300">
                          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0" />
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null
              })()}
              {item.skip_reason && (
                <div>
                  <span className="text-xs font-medium text-gray-400">スキップ理由</span>
                  <p className="mt-0.5 text-gray-700 dark:text-gray-300">{item.skip_reason}</p>
                </div>
              )}
              {item.lot_reason && (
                <div>
                  <span className="text-xs font-medium text-gray-400">ロット根拠（AI）</span>
                  <p className="mt-0.5 text-gray-700 dark:text-gray-300">{item.lot_reason}</p>
                </div>
              )}
              <div className="pt-2 border-t dark:border-gray-700 space-y-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <ScoreBar
                    label="買いスコア"
                    score={item.buy_score}
                    active={!isSkip && !isHold && item.side === 'BUY'}
                    color="green"
                  />
                  <ScoreBar
                    label="売りスコア"
                    score={item.sell_score}
                    active={!isSkip && !isHold && item.side === 'SELL'}
                    color="red"
                  />
                </div>
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div>
                    <span className="text-gray-400">確信度</span>
                    <p className="font-medium mt-0.5">{item.confidence != null ? `${(item.confidence * 100).toFixed(0)}%` : '-'}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">AIセンチメント</span>
                    <p className="font-medium mt-0.5">{item.ai_sentiment != null ? (item.ai_sentiment > 0 ? '+' : '') + item.ai_sentiment.toFixed(1) : '-'}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">参照ニュース数</span>
                    <p className="font-medium mt-0.5">{item.ai_news_count ?? '-'}</p>
                  </div>
                </div>
              </div>
              {!isSkip && !isHold && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2 border-t dark:border-gray-700 text-xs">
                  <div>
                    <span className="text-gray-400">SL</span>
                    <p className="font-medium mt-0.5">{item.stop_loss != null ? item.stop_loss.toFixed(3) : '-'}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">TP</span>
                    <p className="font-medium mt-0.5">{item.take_profit != null ? item.take_profit.toFixed(3) : '-'}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">ステータス</span>
                    <p className="font-medium mt-0.5">{item.status ?? '-'}</p>
                  </div>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ─── ニュース行（展開） ──────────────────────────────────────────────────────

function NewsRow({ item }: { item: NewsItem }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b dark:border-gray-700 last:border-0">
      <button
        className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              {signalBadge(item.signal)}
              {sentimentBadge(item.sentiment)}
              <span className="text-xs text-gray-400">
                {new Date(item.published_at).toLocaleString('ja-JP', {
                  month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
                })}
              </span>
            </div>
            <p className="text-sm font-medium text-gray-800 dark:text-gray-200 leading-snug line-clamp-2">
              {item.title}
            </p>
          </div>
          <div className="flex-shrink-0 pt-0.5">
            {open ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
          </div>
        </div>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{item.summary}</p>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <span className="text-gray-400">センチメント</span>
              <div className="mt-1">{sentimentBar(item.sentiment)}</div>
            </div>
            <div>
              <span className="text-gray-400">USD/JPY インパクト</span>
              <div className="mt-1">{impactDots(item.impact_usdjpy)}</div>
            </div>
            <div>
              <span className="text-gray-400">EUR/JPY インパクト</span>
              <div className="mt-1">{impactDots(item.impact_eurjpy)}</div>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span>時間軸: {item.time_horizon}</span>
            {item.url && (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline"
                onClick={e => e.stopPropagation()}
              >
                元記事を開く →
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── ページ本体 ───────────────────────────────────────────────────────────────

export function DashboardPage() {
  const queryClient = useQueryClient()
  const { data: account, isLoading: accountLoading, error: accountError } = useAccount()
  const { data: positions = [], isLoading: positionsLoading, error: positionsError } = usePositions()
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth()
  const { data: tradeHistory = [], isLoading: historyLoading } = useTradeHistory(30)
  const { data: monthly } = useMonthlySummary()
  const { data: newsList = [], isLoading: newsLoading } = useNews(15)

  const loading = accountLoading || positionsLoading || healthLoading
  const error = accountError || positionsError || healthError
  const isMaintenance = error?.message === 'MAINTENANCE'

  const refetch = () => {
    queryClient.invalidateQueries({ queryKey: ['account'] })
    queryClient.invalidateQueries({ queryKey: ['positions'] })
    queryClient.invalidateQueries({ queryKey: ['health'] })
    queryClient.invalidateQueries({ queryKey: ['tradeHistory'] })
    queryClient.invalidateQueries({ queryKey: ['monthlySummary'] })
    queryClient.invalidateQueries({ queryKey: ['news'] })
  }

  const marginRatio = account?.margin && account?.equity
    ? (parseFloat(account.equity) / parseFloat(account.margin)) * 100
    : null

  const getRiskLevel = (ratio: number | null) => {
    if (ratio === null) return { level: '不明', color: 'text-gray-500 dark:text-gray-400', bgColor: 'bg-gray-100 dark:bg-gray-800' }
    if (ratio >= 300) return { level: '安全', color: 'text-green-600 dark:text-green-400', bgColor: 'bg-green-100 dark:bg-green-900' }
    if (ratio >= 150) return { level: '通常', color: 'text-yellow-600 dark:text-yellow-400', bgColor: 'bg-yellow-100 dark:bg-yellow-900' }
    return { level: '警告', color: 'text-red-600 dark:text-red-400', bgColor: 'bg-red-100 dark:bg-red-900' }
  }
  const riskStatus = getRiskLevel(marginRatio)

  // 直近3件（HOLD/SKIPも含む）
  const recentJudgments = tradeHistory.slice(0, 3)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

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
                ? 'GMOコイン メンテナンス中。終了後は手動で更新してください。'
                : error.message}
            </span>
            <Button variant="outline" size="sm" onClick={refetch}>再試行</Button>
          </div>
        )}

        <div className="space-y-6">

          {/* ① 直近の判断ログ */}
          <section>
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 flex items-center gap-1.5">
              <History className="h-4 w-4" />
              直近の判断ログ
            </h2>
            {historyLoading ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" />読み込み中...
              </div>
            ) : recentJudgments.length === 0 ? (
              <Card><CardContent className="py-8 text-center text-gray-400 text-sm">判断ログなし</CardContent></Card>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {recentJudgments.map(item => (
                  <JudgmentCard key={item.trade_id} item={item} />
                ))}
              </div>
            )}
          </section>

          {/* ② 取引履歴テーブル */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <History className="h-4 w-4" />
                取引履歴
                <span className="text-xs font-normal text-gray-400">（直近30件 / クリックで詳細表示）</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {historyLoading ? (
                <div className="text-center py-8 text-gray-400 text-sm">
                  <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" />読み込み中...
                </div>
              ) : tradeHistory.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">履歴なし</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead>
                      <tr className="border-b dark:border-gray-700">
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">日時</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">通貨ペア</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">判断</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">ロット</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">エントリー値</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">損益</th>
                        <th className="px-4 py-3 w-8"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {tradeHistory.map(item => (
                        <HistoryRow key={item.trade_id} item={item} />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* ③ 最新ニュース */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Newspaper className="h-4 w-4" />
                最新ニュース
                <span className="text-xs font-normal text-gray-400">（直近15件 / クリックで詳細表示）</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {newsLoading ? (
                <div className="text-center py-8 text-gray-400 text-sm">
                  <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" />読み込み中...
                </div>
              ) : newsList.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">ニュースなし</div>
              ) : (
                <div>
                  {newsList.map(item => <NewsRow key={item.news_id} item={item} />)}
                </div>
              )}
            </CardContent>
          </Card>

          {/* ④ 月次サマリー */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <BarChart2 className="h-4 w-4" />
                月次サマリー
                {monthly && (
                  <span className="text-xs font-normal text-gray-400">（{monthly.period}）</span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!monthly ? (
                <div className="text-center py-4 text-gray-400 text-sm">読み込み中...</div>
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

          {/* ⑤ 口座情報 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Wallet className="h-4 w-4" />
                口座情報
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-4 text-gray-400 text-sm">読み込み中...</div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">残高</p>
                    <p className="text-lg font-bold">{formatCurrency(account?.balance)}</p>
                    <p className="text-xs text-gray-400">利用可能: {formatCurrency(account?.availableAmount)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">有効証拠金</p>
                    <p className="text-lg font-bold">{formatCurrency(account?.equity)}</p>
                    <p className="text-xs text-gray-400">必要証拠金: {formatCurrency(account?.margin)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">含み損益</p>
                    <p className={cn(
                      "text-lg font-bold",
                      account?.profitLoss && parseFloat(account.profitLoss) >= 0
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    )}>
                      {formatCurrency(account?.profitLoss)}
                    </p>
                    <p className="text-xs text-gray-400">{positions.length}ポジション</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">証拠金維持率</p>
                    <p className={cn("text-lg font-bold", riskStatus.color)}>
                      {marginRatio !== null ? `${marginRatio.toFixed(1)}%` : '-'}
                    </p>
                    <span className={cn("text-xs px-2 py-0.5 rounded-full", riskStatus.bgColor, riskStatus.color)}>
                      {riskStatus.level}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* ⑥ システムステータス */}
          <Card>
            <CardContent className="py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "w-2 h-2 rounded-full",
                    health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                  )} />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    システム: {health?.status === 'healthy' ? 'オンライン' : 'オフライン'}
                  </span>
                </div>
                <Button variant="outline" size="sm" onClick={refetch} disabled={loading}>
                  <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                  手動更新
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* ⑦ オープンポジション */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Activity className="h-4 w-4" />
                オープンポジション
              </CardTitle>
            </CardHeader>
            <CardContent>
              {positions.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
                  ポジションなし
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead>
                      <tr className="border-b dark:border-gray-700">
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">通貨ペア</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">売買</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">数量</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">エントリー値</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">損益</th>
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
                            <span className={cn(
                              "px-2 py-1 rounded text-xs font-medium",
                              position.side === 'BUY'
                                ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300'
                                : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-300'
                            )}>
                              {position.side === 'BUY' ? '買' : '売'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{position.size}</td>
                          <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{position.price}</td>
                          <td className={cn(
                            "px-4 py-3 text-sm font-medium text-right",
                            parseFloat(position.lossGain) >= 0
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-red-600 dark:text-red-400'
                          )}>
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
      </main>

      <Footer />
    </div>
  )
}
