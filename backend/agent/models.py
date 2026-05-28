from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RobinhoodStep(BaseModel):
    step: int
    instruction: str


class TradeRecommendation(BaseModel):
    ticker: str
    company_name: str
    signal: SignalType
    signal_detail: str
    current_price: float
    entry_low: float
    entry_high: float
    target_price: float
    target_pct: float
    stop_loss: float
    stop_loss_pct: float
    risk_reward_ratio: str
    confidence: ConfidenceLevel
    reasoning: str
    robinhood_steps: list[RobinhoodStep]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DailyDigest(BaseModel):
    date: str
    recommendations: list[TradeRecommendation]
    market_summary: str
    disclaimer: str = (
        "⚠️ RobiAgent is an AI-powered analysis tool and does NOT constitute "
        "licensed financial advice. All trades carry risk. Never invest more "
        "than you can afford to lose. Consult a licensed financial advisor "
        "before making investment decisions."
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TickerMetrics(BaseModel):
    ticker: str
    company_name: str
    current_price: float
    price_change_pct: float
    volume: int
    avg_volume: int
    volume_ratio: float
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    sma_50: float
    sma_200: float
    golden_cross: bool       # 50-day crossed above 200-day
    death_cross: bool        # 50-day crossed below 200-day
    above_50sma: bool
    above_200sma: bool
    news_sentiment: float    # -1.0 to 1.0
    news_headlines: list[str]


class PerformanceRecord(BaseModel):
    id: str
    date: str
    ticker: str
    signal: SignalType
    entry_price: float
    target_price: float
    stop_loss: float
    current_price: Optional[float] = None
    outcome: Optional[str] = None   # "hit_target", "hit_stop", "open", "expired"
    pct_change: Optional[float] = None
    confidence: ConfidenceLevel
