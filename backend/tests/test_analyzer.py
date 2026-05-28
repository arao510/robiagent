import pytest
import json
from unittest.mock import patch, MagicMock
from agent.analyzer import analyze_ticker, build_analysis_prompt
from agent.models import SignalType, ConfidenceLevel


MOCK_CLAUDE_RESPONSE = {
    "signal": "Bullish",
    "signal_detail": "Golden Cross with RSI recovery from oversold territory",
    "entry_low": 193.00,
    "entry_high": 196.00,
    "target_price": 208.00,
    "stop_loss": 188.00,
    "risk_reward_ratio": "1:1.7",
    "confidence": "High",
    "reasoning": "AAPL shows strong technical confluence with a golden cross formation and above-average volume. RSI at 42 indicates room to run before overbought territory.",
    "robinhood_steps": [
        {"step": 1, "instruction": "Open Robinhood → Search $AAPL"},
        {"step": 2, "instruction": "Tap 'Buy' → Select 'Limit Order'"},
        {"step": 3, "instruction": "Set limit price to $194.50"},
        {"step": 4, "instruction": "Set quantity based on your position sizing (risk no more than 2% of portfolio)"},
        {"step": 5, "instruction": "Enable 'Good Till Canceled' and tap 'Review Order' to confirm"},
    ]
}


def make_mock_anthropic_response(data: dict):
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = json.dumps(data)
    mock_response.content = [mock_content]
    return mock_response


class TestAnalyzeTicker:
    @patch("agent.analyzer.client")
    def test_returns_recommendation_on_valid_response(self, mock_client, bullish_metrics):
        mock_client.messages.create.return_value = make_mock_anthropic_response(MOCK_CLAUDE_RESPONSE)
        rec = analyze_ticker(bullish_metrics, score=82.0)

        assert rec is not None
        assert rec.ticker == "AAPL"
        assert rec.signal == SignalType.BULLISH
        assert rec.confidence == ConfidenceLevel.HIGH

    @patch("agent.analyzer.client")
    def test_target_pct_computed_correctly(self, mock_client, bullish_metrics):
        mock_client.messages.create.return_value = make_mock_anthropic_response(MOCK_CLAUDE_RESPONSE)
        rec = analyze_ticker(bullish_metrics, score=82.0)

        expected_pct = round(((208.00 - 195.50) / 195.50) * 100, 2)
        assert abs(rec.target_pct - expected_pct) < 0.1

    @patch("agent.analyzer.client")
    def test_stop_loss_pct_is_negative(self, mock_client, bullish_metrics):
        mock_client.messages.create.return_value = make_mock_anthropic_response(MOCK_CLAUDE_RESPONSE)
        rec = analyze_ticker(bullish_metrics, score=82.0)
        assert rec.stop_loss_pct < 0

    @patch("agent.analyzer.client")
    def test_robinhood_steps_have_5_items(self, mock_client, bullish_metrics):
        mock_client.messages.create.return_value = make_mock_anthropic_response(MOCK_CLAUDE_RESPONSE)
        rec = analyze_ticker(bullish_metrics, score=82.0)
        assert len(rec.robinhood_steps) == 5

    @patch("agent.analyzer.client")
    def test_steps_are_ordered_correctly(self, mock_client, bullish_metrics):
        mock_client.messages.create.return_value = make_mock_anthropic_response(MOCK_CLAUDE_RESPONSE)
        rec = analyze_ticker(bullish_metrics, score=82.0)
        step_numbers = [s.step for s in rec.robinhood_steps]
        assert step_numbers == [1, 2, 3, 4, 5]

    @patch("agent.analyzer.client")
    def test_returns_none_on_api_error(self, mock_client, bullish_metrics):
        mock_client.messages.create.side_effect = Exception("API timeout")
        rec = analyze_ticker(bullish_metrics, score=82.0)
        assert rec is None

    @patch("agent.analyzer.client")
    def test_handles_malformed_json_gracefully(self, mock_client, bullish_metrics):
        bad_response = MagicMock()
        bad_content = MagicMock()
        bad_content.text = "This is not JSON at all"
        bad_response.content = [bad_content]
        mock_client.messages.create.return_value = bad_response

        rec = analyze_ticker(bullish_metrics, score=82.0)
        assert rec is None

    def test_prompt_contains_ticker(self, bullish_metrics):
        prompt = build_analysis_prompt(bullish_metrics, 82.0)
        assert "AAPL" in prompt

    def test_prompt_contains_key_indicators(self, bullish_metrics):
        prompt = build_analysis_prompt(bullish_metrics, 82.0)
        assert "RSI" in prompt
        assert "MACD" in prompt
        assert "Golden Cross" in prompt
