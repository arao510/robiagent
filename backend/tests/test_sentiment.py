import pytest
from agent.sentiment import keyword_sentiment, fetch_news_sentiment
from unittest.mock import patch


class TestKeywordSentiment:
    def test_positive_headline_scores_positive(self):
        score = keyword_sentiment("Apple stock surge rally record earnings beat")
        assert score > 0

    def test_negative_headline_scores_negative(self):
        score = keyword_sentiment("Tesla stock crash plunge loss decline warning")
        assert score < 0

    def test_neutral_headline_scores_zero(self):
        score = keyword_sentiment("Company announces quarterly meeting date")
        assert score == 0.0

    def test_score_bounded_minus_one_to_one(self):
        for text in [
            "surge rally gain record beat profit growth",
            "crash plunge loss decline warning bearish",
            "the quick brown fox jumped over the lazy dog",
        ]:
            score = keyword_sentiment(text)
            assert -1.0 <= score <= 1.0

    def test_mixed_sentiment_is_between_extremes(self):
        score = keyword_sentiment("strong growth but declining margins and loss concern")
        assert -1.0 < score < 1.0


class TestFetchNewsSentiment:
    def test_returns_zero_sentiment_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            sentiment, headlines = fetch_news_sentiment("AAPL", "Apple Inc.")
        assert sentiment == 0.0
        assert headlines == []

    @patch("agent.sentiment.NewsApiClient")
    def test_aggregates_multiple_headlines(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.get_everything.return_value = {
            "articles": [
                {"title": "Apple stock surges on strong earnings beat"},
                {"title": "iPhone sales rally in emerging markets"},
                {"title": "Apple faces lawsuit over patent"},
            ]
        }
        with patch.dict("os.environ", {"NEWS_API_KEY": "fake_key"}):
            sentiment, headlines = fetch_news_sentiment("AAPL", "Apple Inc.")

        assert isinstance(sentiment, float)
        assert -1.0 <= sentiment <= 1.0
        assert len(headlines) <= 5

    @patch("agent.sentiment.NewsApiClient")
    def test_handles_api_error_gracefully(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.get_everything.side_effect = Exception("Rate limit exceeded")

        with patch.dict("os.environ", {"NEWS_API_KEY": "fake_key"}):
            sentiment, headlines = fetch_news_sentiment("AAPL", "Apple Inc.")

        assert sentiment == 0.0
        assert headlines == []
