import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from agent.models import (
    TickerMetrics, TradeRecommendation, DailyDigest,
    SignalType, ConfidenceLevel, RobinhoodStep
)


def make_price_series(n=252, start=150.0, trend=0.001, noise=0.015) -> pd.Series:
    """Generate a synthetic price series for testing."""
    np.random.seed(42)
    changes = np.random.normal(trend, noise, n)
    prices = [start]
    for c in changes:
        prices.append(prices[-1] * (1 + c))
    return pd.Series(prices[:n], name="Close")


def make_volume_series(n=252, avg=5_000_000) -> pd.Series:
    np.random.seed(42)
    return pd.Series(
        np.random.randint(int(avg * 0.5), int(avg * 2.0), n),
        name="Volume"
    )


@pytest.fixture
def bullish_metrics() -> TickerMetrics:
    return TickerMetrics(
        ticker="AAPL",
        company_name="Apple Inc.",
        current_price=195.50,
        price_change_pct=1.8,
        volume=82_000_000,
        avg_volume=55_000_000,
        volume_ratio=1.49,
        rsi=42.5,
        macd=0.85,
        macd_signal=0.60,
        macd_histogram=0.25,
        sma_50=190.20,
        sma_200=178.40,
        golden_cross=True,
        death_cross=False,
        above_50sma=True,
        above_200sma=True,
        news_sentiment=0.45,
        news_headlines=["Apple beats earnings expectations", "iPhone demand surges in Asia"],
    )


@pytest.fixture
def bearish_metrics() -> TickerMetrics:
    return TickerMetrics(
        ticker="TSLA",
        company_name="Tesla Inc.",
        current_price=210.00,
        price_change_pct=-3.2,
        volume=90_000_000,
        avg_volume=70_000_000,
        volume_ratio=1.28,
        rsi=71.0,
        macd=-0.40,
        macd_signal=-0.10,
        macd_histogram=-0.30,
        sma_50=225.00,
        sma_200=235.00,
        golden_cross=False,
        death_cross=True,
        above_50sma=False,
        above_200sma=False,
        news_sentiment=-0.35,
        news_headlines=["Tesla misses delivery targets", "EV demand concerns grow"],
    )


@pytest.fixture
def neutral_metrics() -> TickerMetrics:
    return TickerMetrics(
        ticker="MSFT",
        company_name="Microsoft Corp.",
        current_price=415.00,
        price_change_pct=0.1,
        volume=20_000_000,
        avg_volume=22_000_000,
        volume_ratio=0.91,
        rsi=52.0,
        macd=0.05,
        macd_signal=0.04,
        macd_histogram=0.01,
        sma_50=412.00,
        sma_200=390.00,
        golden_cross=False,
        death_cross=False,
        above_50sma=True,
        above_200sma=True,
        news_sentiment=0.05,
        news_headlines=[],
    )


@pytest.fixture
def sample_recommendation() -> TradeRecommendation:
    return TradeRecommendation(
        ticker="AAPL",
        company_name="Apple Inc.",
        signal=SignalType.BULLISH,
        signal_detail="Golden Cross with RSI recovering from oversold",
        current_price=195.50,
        entry_low=193.00,
        entry_high=196.00,
        target_price=208.00,
        target_pct=6.4,
        stop_loss=188.00,
        stop_loss_pct=-3.8,
        risk_reward_ratio="1:1.7",
        confidence=ConfidenceLevel.HIGH,
        reasoning="Strong confluence of golden cross, above-average volume, and positive earnings sentiment.",
        robinhood_steps=[
            RobinhoodStep(step=1, instruction="Open Robinhood → Search $AAPL"),
            RobinhoodStep(step=2, instruction="Tap 'Buy' → Select 'Limit Order'"),
            RobinhoodStep(step=3, instruction="Set limit price to $194.50"),
            RobinhoodStep(step=4, instruction="Set quantity based on your position sizing"),
            RobinhoodStep(step=5, instruction="Enable 'Good Till Canceled' and confirm"),
        ],
    )


@pytest.fixture
def sample_digest(sample_recommendation) -> DailyDigest:
    return DailyDigest(
        date="2024-01-15",
        recommendations=[sample_recommendation],
        market_summary="Markets show selective bullish momentum. AAPL leads on technical strength.",
    )
