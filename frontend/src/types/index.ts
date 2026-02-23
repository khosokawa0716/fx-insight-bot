// Account types
export interface AccountData {
  balance: string
  availableAmount: string
  margin: string
  profitLoss: string
  equity: string
}

// Position types
export interface Position {
  positionId: string
  symbol: string
  side: 'BUY' | 'SELL'
  size: string
  price: string
  lossGain: string
  timestamp: string
}

// Health types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  gcp_project?: string
  firestore_db?: string
  location?: string
}

// API Response types
export interface ApiResponse<T> {
  status: 'success' | 'error'
  data?: T
  message?: string
}

export interface PositionsResponse {
  status: 'success' | 'error'
  count: number
  positions: Position[]
}

// News types
export interface NewsItem {
  news_id: string
  title: string
  summary: string
  url: string
  sentiment: number  // -2 to 2
  impact_usdjpy: number  // 1 to 5
  impact_eurjpy: number  // 1 to 5
  time_horizon: 'immediate' | 'short-term' | 'medium-term' | 'long-term'
  signal: 'BUY_CANDIDATE' | 'SELL_CANDIDATE' | 'RISK_OFF' | 'IGNORE'
  published_at: string
  collected_at: string
}

export interface NewsListResponse {
  status: 'success' | 'error'
  count: number
  news: NewsItem[]
}

// Monthly Summary types
export interface MonthlySummaryData {
  total_trades: number
  win_count: number
  loss_count: number
  win_rate: number
  skip_count: number
  actual_pnl: number
  baseline_pnl: number
  ai_advantage: number
  lot_stats: Record<string, { count: number; win: number; loss: number; pnl: number }>
}

export interface MonthlySummaryResponse {
  status: 'success' | 'error'
  period: string
  data: MonthlySummaryData
}

// Trade History types
export type TradeAction = 'BUY' | 'SELL' | 'HOLD' | 'SKIP'

export interface TradeHistoryItem {
  trade_id: string
  symbol: string
  side: string
  used_lot: number
  reason: string
  created_at: string
  dry_run: boolean
  entry_price?: number | null
  stop_loss?: number | null
  take_profit?: number | null
  order_id?: string | null
  status?: string | null
  actual_pnl?: number | null
  baseline_pnl?: number | null
  ai_sentiment?: number | null
  ai_impact?: number | null
  ai_news_count?: number | null
  lot_reason?: string | null
  buy_score?: number | null
  sell_score?: number | null
  confidence?: number | null
  skip_reason?: string | null
}

export interface TradeHistoryResponse {
  status: 'success' | 'error'
  count: number
  items: TradeHistoryItem[]
}

// Signal types
export interface SignalItem {
  news_id: string
  title: string
  summary: string
  signal: 'BUY_CANDIDATE' | 'SELL_CANDIDATE' | 'RISK_OFF'
  sentiment: number
  impact_usdjpy: number
  impact_eurjpy: number
  time_horizon: 'immediate' | 'short-term' | 'medium-term' | 'long-term'
  published_at: string
}

export interface SignalListResponse {
  status: 'success' | 'error'
  count: number
  signals: SignalItem[]
}
