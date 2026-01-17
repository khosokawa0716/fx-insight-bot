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
