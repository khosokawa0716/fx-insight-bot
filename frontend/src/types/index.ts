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
