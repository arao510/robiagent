# RobiAgent 🤖📈

An AI-powered stock analysis tool that runs every morning, scans your watchlist, and delivers the top trade opportunities of the day — complete with entry prices, targets, stop-losses, and step-by-step Robinhood execution instructions.

---

## What It Does

Every day RobiAgent:
1. Pulls real market data for 10 stocks (AAPL, TSLA, NVDA, etc.)
2. Scores each stock using technical indicators (RSI, MACD, moving averages, volume)
3. Sends the top 5 candidates to GPT-4o for deep analysis
4. Displays structured trade recommendations on a clean dashboard
5. Tracks how each recommendation performs over time

---

## How It Works (Layer by Layer)

```
You click "Run Analysis"
        ↓
FastAPI backend receives the request
        ↓
Orchestrator loops through your watchlist
        ↓
yfinance fetches price/volume data → computes RSI, MACD, SMAs, volume ratio
        ↓
NewsAPI fetches headlines → scores sentiment for each ticker
        ↓
Scoring algorithm ranks all tickers 0–100
        ↓
Top 5 tickers get sent to GPT-4o for analysis
        ↓
GPT-4o returns entry range, target, stop-loss, reasoning, Robinhood steps
        ↓
Results saved to disk → React dashboard displays recommendations
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend | Python + FastAPI |
| AI Analysis | GPT-4o (OpenAI) |
| Market Data | yfinance |
| News Sentiment | NewsAPI |
| Scheduling | APScheduler (runs daily at 7AM UTC) |
| Charts | Recharts |
| Testing | PyTest (27 tests) |
| CI/CD | GitHub Actions |

---

## Project Structure

```
robiagent/
├── backend/
│   ├── agent/
│   │   ├── models.py          # Data structures (recommendations, digests)
│   │   ├── market_data.py     # yfinance + technical indicator calculations
│   │   ├── sentiment.py       # News fetching + sentiment scoring
│   │   ├── analyzer.py        # GPT-4o analysis layer
│   │   └── orchestrator.py    # Main pipeline that connects everything
│   ├── api/
│   │   └── main.py            # FastAPI routes + daily scheduler
│   ├── tests/                 # 27 PyTest test cases
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── App.tsx            # Main dashboard UI
│       ├── hooks/useApi.ts    # API calls to backend
│       └── types/index.ts     # TypeScript type definitions
└── .github/workflows/ci.yml   # GitHub Actions CI pipeline
```

---

## Getting Started

### What You Need
- Python 3.11+
- Node.js 18+
- An OpenAI API key → [platform.openai.com](https://platform.openai.com)
- A NewsAPI key (free) → [newsapi.org](https://newsapi.org)

### 1. Download and enter the project
```bash
cd robiagent
```

### 2. Set up the backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Add your API keys
```bash
cp .env.example .env
```
Open `.env` and fill in:
```
OPENAI_API_KEY=sk-your-key-here
NEWS_API_KEY=your-news-key-here
```

### 4. Start the backend
```bash
uvicorn api.main:app --reload --port 8000
```
You should see: `Application startup complete`

### 5. Start the frontend (new terminal tab)
```bash
cd frontend
npm install
npm run dev
```

### 6. Open the app
Go to **http://localhost:5173** in your browser, then click **"Run Analysis"**.

Wait about 60 seconds for the first results to appear.

---

## API Endpoints

| Method | Endpoint | What It Does |
|---|---|---|
| POST | `/api/run` | Trigger a fresh analysis |
| GET | `/api/digest/latest` | Get today's recommendations |
| GET | `/api/digest/history` | Get all past digests |
| GET | `/api/performance` | Get trade outcome tracking |
| GET | `/api/health` | Check scheduler status |

---

## Running the Tests

```bash
cd backend
pytest tests/ -v
```

Tests cover:
- Scoring algorithm (10 tests) — verifies bullish/bearish/neutral signals score correctly
- GPT-4o analyzer (9 tests) — uses mocked API responses to test parsing and error handling
- Sentiment scoring (5 tests) — verifies keyword sentiment logic
- API endpoints (3 tests) — verifies routes return correct responses

---

## What Each Recommendation Includes

```
Ticker: TSLA
Signal: Bullish — Golden Cross with above-average volume
Current Price: $443.30
Entry Range: $435.00 – $445.00
Target: $475.00 (+7.2%)
Stop Loss: $425.00 (-4.1%)
Risk/Reward: 1:3.0
Confidence: Medium
Reasoning: Tesla is showing bullish momentum with price above both
           the 50 and 200-day SMAs...

Robinhood Execution Guide:
  1. Log in to your Robinhood account
  2. Search for 'TSLA' in the search bar
  3. Click 'Buy' and choose a limit order type
  4. Set your entry price between $435 and $445
  5. Set stop loss at $425 and target sell at $475
```

---

## Customizing Your Watchlist

Edit the `WATCHLIST` variable in your `.env` file:
```
WATCHLIST=AAPL,MSFT,NVDA,TSLA,AMZN,GOOGL,META,AMD,PLTR,SOFI
```

Add or remove any tickers you want — separated by commas, no spaces.

---

## Disclaimer

> ⚠️ RobiAgent is an AI-powered analysis tool and does **NOT** constitute licensed financial advice. All trades carry risk. Never invest more than you can afford to lose. Consult a licensed financial advisor before making investment decisions.