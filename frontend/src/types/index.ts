export type SignalType = 'Bullish' | 'Bearish' | 'Neutral'
export type ConfidenceLevel = 'High' | 'Medium' | 'Low'
export type OutcomeType = 'hit_target' | 'hit_stop' | 'open' | 'expired'

export interface RobinhoodStep {
  step: number
  instruction: string
}

export interface TradeRecommendation {
  ticker: string
  company_name: string
  signal: SignalType
  signal_detail: string
  current_price: number
  entry_low: number
  entry_high: number
  target_price: number
  target_pct: number
  stop_loss: number
  stop_loss_pct: number
  risk_reward_ratio: string
  confidence: ConfidenceLevel
  reasoning: string
  robinhood_steps: RobinhoodStep[]
  generated_at: string
}

export interface DailyDigest {
  date: string
  recommendations: TradeRecommendation[]
  market_summary: string
  disclaimer: string
  generated_at: string
}

export interface PerformanceRecord {
  id: string
  date: string
  ticker: string
  signal: SignalType
  entry_price: number
  target_price: number
  stop_loss: number
  current_price?: number
  outcome?: OutcomeType
  pct_change?: number
  confidence: ConfidenceLevel
}
