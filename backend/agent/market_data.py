import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD
from typing import Optional
import logging

from .models import TickerMetrics

logger = logging.getLogger(__name__)


def compute_metrics(ticker: str, news_sentiment: float = 0.0, news_headlines: list[str] = []) -> Optional[TickerMetrics]:
    """
    Fetch OHLCV data and compute all technical indicators for a ticker.
    Returns None if data is unavailable.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Fetch 1 year of daily data for indicator calculations
        hist = stock.history(period="1y")
        if hist.empty or len(hist) < 50:
            logger.warning(f"Insufficient data for {ticker}")
            return None

        close = hist["Close"]
        volume = hist["Volume"]

        # --- RSI (14-period) ---
        rsi_indicator = RSIIndicator(close=close, window=14)
        rsi = float(rsi_indicator.rsi().iloc[-1])

        # --- MACD (12, 26, 9) ---
        macd_indicator = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
        macd_val = float(macd_indicator.macd().iloc[-1])
        macd_signal = float(macd_indicator.macd_signal().iloc[-1])
        macd_hist = float(macd_indicator.macd_diff().iloc[-1])

        # --- Moving Averages ---
        sma_50 = float(close.rolling(window=50).mean().iloc[-1])
        sma_200 = float(close.rolling(window=200).mean().iloc[-1])

        # Golden/Death Cross: detect crossover in last 5 days
        sma_50_series = close.rolling(window=50).mean()
        sma_200_series = close.rolling(window=200).mean()
        recent_50 = sma_50_series.iloc[-5:]
        recent_200 = sma_200_series.iloc[-5:]
        golden_cross = bool(
            (recent_50.iloc[-1] > recent_200.iloc[-1]) and
            (recent_50.iloc[0] <= recent_200.iloc[0])
        )
        death_cross = bool(
            (recent_50.iloc[-1] < recent_200.iloc[-1]) and
            (recent_50.iloc[0] >= recent_200.iloc[0])
        )

        # --- Price & Volume ---
        current_price = float(close.iloc[-1])
        prev_close = float(close.iloc[-2])
        price_change_pct = round(((current_price - prev_close) / prev_close) * 100, 2)

        current_volume = int(volume.iloc[-1])
        avg_volume = int(volume.rolling(window=20).mean().iloc[-1])
        volume_ratio = round(current_volume / avg_volume, 2) if avg_volume > 0 else 1.0

        company_name = info.get("longName") or info.get("shortName") or ticker

        return TickerMetrics(
            ticker=ticker,
            company_name=company_name,
            current_price=round(current_price, 2),
            price_change_pct=price_change_pct,
            volume=current_volume,
            avg_volume=avg_volume,
            volume_ratio=volume_ratio,
            rsi=round(rsi, 2),
            macd=round(macd_val, 4),
            macd_signal=round(macd_signal, 4),
            macd_histogram=round(macd_hist, 4),
            sma_50=round(sma_50, 2),
            sma_200=round(sma_200, 2),
            golden_cross=golden_cross,
            death_cross=death_cross,
            above_50sma=current_price > sma_50,
            above_200sma=current_price > sma_200,
            news_sentiment=round(news_sentiment, 3),
            news_headlines=news_headlines,
        )

    except Exception as e:
        logger.error(f"Error computing metrics for {ticker}: {e}")
        return None


def score_ticker(metrics: TickerMetrics) -> float:
    """
    Score a ticker 0–100 based on signal confluence.
    Higher = stronger bullish opportunity.
    """
    score = 50.0  # neutral baseline

    # RSI: oversold = buying opportunity (30–50 range is sweet spot for entries)
    if 30 <= metrics.rsi <= 50:
        score += 10
    elif metrics.rsi < 30:
        score += 15  # oversold, strong signal
    elif metrics.rsi > 70:
        score -= 10  # overbought

    # MACD: positive histogram = bullish momentum
    if metrics.macd_histogram > 0:
        score += 8
    elif metrics.macd_histogram < 0:
        score -= 8

    # MACD crossover (macd line above signal)
    if metrics.macd > metrics.macd_signal:
        score += 7

    # Moving average position
    if metrics.above_50sma:
        score += 5
    if metrics.above_200sma:
        score += 5

    # Golden / Death cross — strong signals
    if metrics.golden_cross:
        score += 15
    if metrics.death_cross:
        score -= 15

    # Volume confirmation
    if metrics.volume_ratio >= 1.5:
        score += 8
    elif metrics.volume_ratio >= 1.2:
        score += 4

    # News sentiment
    score += metrics.news_sentiment * 10

    return round(min(max(score, 0), 100), 1)
