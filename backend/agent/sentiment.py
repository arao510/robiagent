import os
import logging
from newsapi import NewsApiClient
from typing import Optional

logger = logging.getLogger(__name__)

# Simple keyword sentiment scoring (fallback if no API key)
POSITIVE_WORDS = {
    "surge", "rally", "gain", "record", "beat", "profit", "growth",
    "upgrade", "strong", "bullish", "upbeat", "positive", "rise",
    "boost", "exceed", "outperform", "breakthrough", "soar"
}
NEGATIVE_WORDS = {
    "fall", "drop", "loss", "miss", "decline", "downgrade", "bearish",
    "weak", "negative", "cut", "layoff", "lawsuit", "crash", "plunge",
    "concern", "risk", "sell", "tumble", "warning", "miss"
}


def keyword_sentiment(text: str) -> float:
    """Score sentiment -1 to 1 using keyword matching."""
    words = set(text.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)


def fetch_news_sentiment(ticker: str, company_name: str) -> tuple[float, list[str]]:
    """
    Fetch recent news headlines and compute aggregate sentiment score.
    Returns (sentiment_score, headlines_list).
    sentiment_score: -1.0 (very negative) to 1.0 (very positive)
    """
    api_key = os.getenv("NEWS_API_KEY")
    headlines = []
    sentiment_scores = []

    if api_key:
        try:
            client = NewsApiClient(api_key=api_key)
            query = f"{ticker} OR {company_name} stock"
            results = client.get_everything(
                q=query,
                language="en",
                sort_by="publishedAt",
                page_size=10,
            )
            articles = results.get("articles", [])
            for article in articles[:10]:
                title = article.get("title", "")
                if title and "[Removed]" not in title:
                    headlines.append(title)
                    sentiment_scores.append(keyword_sentiment(title))
        except Exception as e:
            logger.warning(f"NewsAPI error for {ticker}: {e}")

    # Fallback: no headlines
    if not sentiment_scores:
        return 0.0, []

    avg_sentiment = round(sum(sentiment_scores) / len(sentiment_scores), 3)
    return avg_sentiment, headlines[:5]
