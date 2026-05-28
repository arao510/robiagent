import pytest
from agent.market_data import score_ticker
from agent.models import TickerMetrics


class TestScoreTicker:
    def test_bullish_ticker_scores_high(self, bullish_metrics):
        score = score_ticker(bullish_metrics)
        assert score >= 70, f"Bullish ticker should score >= 70, got {score}"

    def test_bearish_ticker_scores_low(self, bearish_metrics):
        score = score_ticker(bearish_metrics)
        assert score <= 40, f"Bearish ticker should score <= 40, got {score}"

    def test_neutral_ticker_scores_midrange(self, neutral_metrics):
        score = score_ticker(neutral_metrics)
        assert 40 <= score <= 80, f"Neutral ticker should score 40-80, got {score}"

    def test_score_bounded_0_to_100(self, bullish_metrics, bearish_metrics):
        for metrics in [bullish_metrics, bearish_metrics]:
            score = score_ticker(metrics)
            assert 0 <= score <= 100

    def test_golden_cross_boosts_score(self, neutral_metrics):
        base_score = score_ticker(neutral_metrics)
        neutral_metrics.golden_cross = True
        boosted_score = score_ticker(neutral_metrics)
        assert boosted_score > base_score

    def test_death_cross_lowers_score(self, neutral_metrics):
        base_score = score_ticker(neutral_metrics)
        neutral_metrics.death_cross = True
        lowered_score = score_ticker(neutral_metrics)
        assert lowered_score < base_score

    def test_oversold_rsi_boosts_score(self, neutral_metrics):
        neutral_metrics.rsi = 28.0  # oversold
        oversold_score = score_ticker(neutral_metrics)
        neutral_metrics.rsi = 75.0  # overbought
        overbought_score = score_ticker(neutral_metrics)
        assert oversold_score > overbought_score

    def test_high_volume_ratio_boosts_score(self, neutral_metrics):
        neutral_metrics.volume_ratio = 0.5
        low_vol_score = score_ticker(neutral_metrics)
        neutral_metrics.volume_ratio = 2.0
        high_vol_score = score_ticker(neutral_metrics)
        assert high_vol_score > low_vol_score

    def test_positive_news_sentiment_boosts_score(self, neutral_metrics):
        neutral_metrics.news_sentiment = -0.8
        neg_score = score_ticker(neutral_metrics)
        neutral_metrics.news_sentiment = 0.8
        pos_score = score_ticker(neutral_metrics)
        assert pos_score > neg_score

    def test_macd_histogram_positive_boosts_score(self, neutral_metrics):
        neutral_metrics.macd_histogram = -0.5
        neg_score = score_ticker(neutral_metrics)
        neutral_metrics.macd_histogram = 0.5
        pos_score = score_ticker(neutral_metrics)
        assert pos_score > neg_score
