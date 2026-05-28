import os
import json
import logging
from openai import OpenAI
from datetime import datetime

from .models import (
    TickerMetrics, TradeRecommendation, DailyDigest,
    SignalType, ConfidenceLevel, RobinhoodStep
)

logger = logging.getLogger(__name__)
client = OpenAI()  # reads OPENAI_API_KEY from env automatically


ANALYSIS_SYSTEM_PROMPT = """You are RobiAgent, an expert quantitative trading analyst. 
Your job is to analyze technical indicators for stocks and generate precise, actionable 
trade recommendations for retail investors using Robinhood.

You communicate clearly and confidently. You explain complex signals in plain English.
You are data-driven, not speculative. You always acknowledge risk.

When generating recommendations, you must respond with valid JSON only — no markdown, 
no preamble, just the raw JSON object as specified."""


def build_analysis_prompt(metrics: TickerMetrics, score: float) -> str:
    return f"""Analyze this stock and generate a trade recommendation.

TICKER DATA:
- Ticker: {metrics.ticker} ({metrics.company_name})
- Current Price: ${metrics.current_price}
- Price Change Today: {metrics.price_change_pct}%
- Opportunity Score: {score}/100

TECHNICAL INDICATORS:
- RSI (14): {metrics.rsi}
- MACD: {metrics.macd} | Signal: {metrics.macd_signal} | Histogram: {metrics.macd_histogram}
- 50-Day SMA: ${metrics.sma_50} | Price Above: {metrics.above_50sma}
- 200-Day SMA: ${metrics.sma_200} | Price Above: {metrics.above_200sma}
- Golden Cross (bullish): {metrics.golden_cross}
- Death Cross (bearish): {metrics.death_cross}

VOLUME:
- Today's Volume: {metrics.volume:,}
- 20-Day Avg Volume: {metrics.avg_volume:,}
- Volume Ratio: {metrics.volume_ratio}x

NEWS SENTIMENT:
- Score: {metrics.news_sentiment} (range: -1.0 very negative to 1.0 very positive)
- Recent Headlines: {json.dumps(metrics.news_headlines[:3])}

Respond with ONLY this JSON (no extra text):
{{
  "signal": "Bullish" | "Bearish" | "Neutral",
  "signal_detail": "<one line technical summary, e.g. 'Golden Cross with RSI recovery from oversold'>",
  "entry_low": <float — lower bound of entry range>,
  "entry_high": <float — upper bound of entry range>,
  "target_price": <float — realistic 4-8 week target>,
  "stop_loss": <float — stop loss level>,
  "risk_reward_ratio": "<string e.g. '1:2.1'>",
  "confidence": "High" | "Medium" | "Low",
  "reasoning": "<2-3 sentences of plain English reasoning explaining why this trade makes sense now>",
  "robinhood_steps": [
    {{"step": 1, "instruction": "<specific instruction>"}},
    {{"step": 2, "instruction": "<specific instruction>"}},
    {{"step": 3, "instruction": "<specific instruction>"}},
    {{"step": 4, "instruction": "<specific instruction>"}},
    {{"step": 5, "instruction": "<specific instruction>"}}
  ]
}}"""


def build_market_summary_prompt(all_metrics: list[TickerMetrics], top_picks: list[TradeRecommendation]) -> str:
    tickers_analyzed = [m.ticker for m in all_metrics]
    top_tickers = [r.ticker for r in top_picks]
    bullish_count = sum(1 for m in all_metrics if m.macd_histogram > 0 and m.above_50sma)
    return f"""Write a concise 2-3 sentence market summary for today's RobiAgent daily digest.

Tickers analyzed: {tickers_analyzed}
Top picks selected: {top_tickers}
Bullish-leaning tickers in watchlist: {bullish_count}/{len(all_metrics)}
Date: {datetime.utcnow().strftime('%B %d, %Y')}

Keep it factual, confident, and under 60 words. No markdown. Plain text only."""


def analyze_ticker(metrics: TickerMetrics, score: float) -> TradeRecommendation | None:
    """Call GPT-4o to generate a trade recommendation for a single ticker."""
    try:
        prompt = build_analysis_prompt(metrics, score)
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )

        raw = response.choices[0].message.content.strip()
        # Strip any accidental markdown fences
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        current = metrics.current_price
        target = data["target_price"]
        stop = data["stop_loss"]
        target_pct = round(((target - current) / current) * 100, 2)
        stop_pct = round(((stop - current) / current) * 100, 2)

        steps = [
            RobinhoodStep(step=s["step"], instruction=s["instruction"])
            for s in data["robinhood_steps"]
        ]

        return TradeRecommendation(
            ticker=metrics.ticker,
            company_name=metrics.company_name,
            signal=SignalType(data["signal"]),
            signal_detail=data["signal_detail"],
            current_price=current,
            entry_low=data["entry_low"],
            entry_high=data["entry_high"],
            target_price=target,
            target_pct=target_pct,
            stop_loss=stop,
            stop_loss_pct=stop_pct,
            risk_reward_ratio=data["risk_reward_ratio"],
            confidence=ConfidenceLevel(data["confidence"]),
            reasoning=data["reasoning"],
            robinhood_steps=steps,
        )

    except Exception as e:
        logger.error(f"GPT analysis failed for {metrics.ticker}: {e}")
        return None


def generate_market_summary(all_metrics: list[TickerMetrics], top_picks: list[TradeRecommendation]) -> str:
    """Generate a brief market summary via GPT-4o."""
    try:
        prompt = build_market_summary_prompt(all_metrics, top_picks)
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=200,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Market summary generation failed: {e}")
        return "Market analysis complete. See recommendations below."