import os
import json
import logging
import uuid
import time
from datetime import datetime, date
from pathlib import Path

from .models import DailyDigest, PerformanceRecord, TradeRecommendation
from .market_data import compute_metrics, score_ticker
from .sentiment import fetch_news_sentiment
from .analyzer import analyze_ticker, generate_market_summary

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DIGESTS_FILE = DATA_DIR / "digests.json"
PERFORMANCE_FILE = DATA_DIR / "performance.json"


# ---------- Persistence helpers ----------

def _load_json(path: Path) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return []
    return []


def _save_json(path: Path, data: list):
    path.write_text(json.dumps(data, indent=2, default=str))


# ---------- Performance tracking ----------

def save_performance_records(recommendations: list[TradeRecommendation], digest_date: str):
    records = _load_json(PERFORMANCE_FILE)
    for rec in recommendations:
        record = PerformanceRecord(
            id=str(uuid.uuid4()),
            date=digest_date,
            ticker=rec.ticker,
            signal=rec.signal,
            entry_price=rec.current_price,
            target_price=rec.target_price,
            stop_loss=rec.stop_loss,
            outcome="open",
            confidence=rec.confidence,
        )
        records.append(record.model_dump())
    _save_json(PERFORMANCE_FILE, records)


def update_performance_outcomes():
    """Update open performance records with current prices."""
    import yfinance as yf
    records = _load_json(PERFORMANCE_FILE)
    updated = False

    for record in records:
        if record.get("outcome") != "open":
            continue

        ticker = record["ticker"]
        try:
            hist = yf.Ticker(ticker).history(period="1d")
            if hist.empty:
                continue
            current = float(hist["Close"].iloc[-1])
            entry = record["entry_price"]
            target = record["target_price"]
            stop = record["stop_loss"]

            pct = round(((current - entry) / entry) * 100, 2)
            record["current_price"] = round(current, 2)
            record["pct_change"] = pct

            if current >= target:
                record["outcome"] = "hit_target"
            elif current <= stop:
                record["outcome"] = "hit_stop"

            # Expire after 30 days
            rec_date = datetime.fromisoformat(record["date"]) if "T" in record["date"] else datetime.strptime(record["date"], "%Y-%m-%d")
            if (datetime.utcnow() - rec_date).days > 30:
                record["outcome"] = "expired"

            updated = True
        except Exception as e:
            logger.warning(f"Could not update performance for {ticker}: {e}")

    if updated:
        _save_json(PERFORMANCE_FILE, records)

    return records


# ---------- Main agent run ----------

def run_daily_analysis() -> DailyDigest:
    """
    Full pipeline:
    1. Load watchlist
    2. Fetch metrics + sentiment for each ticker
    3. Score and rank tickers
    4. Send top candidates to GPT-4o for deep analysis
    5. Assemble and persist daily digest
    """
    watchlist_raw = os.getenv("WATCHLIST", "AAPL,MSFT,NVDA,TSLA,AMZN")
    watchlist = [t.strip().upper() for t in watchlist_raw.split(",") if t.strip()]
    today = date.today().isoformat()

    logger.info(f"RobiAgent daily run starting — {today} — {len(watchlist)} tickers")

    # Step 1: Gather all metrics
    all_metrics = []
    scored = []

    for ticker in watchlist:
        logger.info(f"Fetching data for {ticker}...")
        sentiment, headlines = fetch_news_sentiment(ticker, ticker)
        metrics = compute_metrics(ticker, sentiment, headlines)
        time.sleep(2)
        if metrics:
            all_metrics.append(metrics)
            score = score_ticker(metrics)
            scored.append((score, metrics))
            logger.info(f"  {ticker}: score={score}, rsi={metrics.rsi}, golden_cross={metrics.golden_cross}")

    # Step 2: Sort by score, take top 5 candidates
    scored.sort(key=lambda x: x[0], reverse=True)
    top_candidates = scored[:5]

    # Step 3: GPT-4o analysis for each candidate
    recommendations = []
    for score, metrics in top_candidates:
        logger.info(f"Analyzing {metrics.ticker} with GPT-4o (score={score})...")
        rec = analyze_ticker(metrics, score)
        if rec:
            recommendations.append(rec)

    # Step 4: Market summary
    market_summary = generate_market_summary(all_metrics, recommendations)

    # Step 5: Assemble digest
    digest = DailyDigest(
        date=today,
        recommendations=recommendations,
        market_summary=market_summary,
    )

    # Step 6: Persist
    digests = _load_json(DIGESTS_FILE)
    digests.append(digest.model_dump())
    _save_json(DIGESTS_FILE, digests)
    save_performance_records(recommendations, today)
    update_performance_outcomes()

    logger.info(f"RobiAgent run complete — {len(recommendations)} recommendations generated")
    return digest


def get_latest_digest() -> DailyDigest | None:
    digests = _load_json(DIGESTS_FILE)
    if not digests:
        return None
    return DailyDigest(**digests[-1])


def get_all_digests() -> list[DailyDigest]:
    digests = _load_json(DIGESTS_FILE)
    return [DailyDigest(**d) for d in digests]


def get_performance_records() -> list[PerformanceRecord]:
    records = _load_json(PERFORMANCE_FILE)
    return [PerformanceRecord(**r) for r in records]