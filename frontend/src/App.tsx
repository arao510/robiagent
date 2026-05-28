import { useState } from 'react'
import { TrendingUp, TrendingDown, Minus, RefreshCw, BarChart3, Clock, AlertTriangle, ChevronDown, ChevronUp, Target, ShieldAlert, Zap } from 'lucide-react'
import { XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, BarChart, Bar } from 'recharts'
import { useLatestDigest, usePerformance, triggerRun } from './hooks/useApi'
import type { TradeRecommendation, PerformanceRecord, SignalType, ConfidenceLevel } from './types'

// ─── Color utils ────────────────────────────────────────────────────────────

const signalColors: Record<SignalType, string> = {
  Bullish: '#00d97e',
  Bearish: '#ff4d6d',
  Neutral: '#7b8fa1',
}

const confidenceColors: Record<ConfidenceLevel, string> = {
  High: '#00d97e',
  Medium: '#f4a22d',
  Low: '#ff4d6d',
}

const outcomeColors: Record<string, string> = {
  hit_target: '#00d97e',
  hit_stop: '#ff4d6d',
  open: '#f4a22d',
  expired: '#7b8fa1',
}

// ─── Signal icon ─────────────────────────────────────────────────────────────

function SignalIcon({ signal }: { signal: SignalType }) {
  const color = signalColors[signal]
  if (signal === 'Bullish') return <TrendingUp size={16} color={color} />
  if (signal === 'Bearish') return <TrendingDown size={16} color={color} />
  return <Minus size={16} color={color} />
}

// ─── Recommendation Card ─────────────────────────────────────────────────────

function RecommendationCard({ rec }: { rec: TradeRecommendation }) {
  const [expanded, setExpanded] = useState(false)
  const sigColor = signalColors[rec.signal]
  const confColor = confidenceColors[rec.confidence]

  return (
    <div className="rec-card">
      <div className="rec-header" onClick={() => setExpanded(e => !e)}>
        <div className="rec-left">
          <span className="rec-ticker">{rec.ticker}</span>
          <span className="rec-company">{rec.company_name}</span>
          <span className="rec-signal" style={{ color: sigColor, borderColor: sigColor }}>
            <SignalIcon signal={rec.signal} />
            {rec.signal}
          </span>
        </div>
        <div className="rec-right">
          <div className="rec-price">${rec.current_price.toFixed(2)}</div>
          <div className="rec-target" style={{ color: rec.target_pct >= 0 ? '#00d97e' : '#ff4d6d' }}>
            {rec.target_pct >= 0 ? '+' : ''}{rec.target_pct.toFixed(1)}%
          </div>
          <span className="rec-conf" style={{ backgroundColor: `${confColor}22`, color: confColor }}>
            {rec.confidence}
          </span>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {expanded && (
        <div className="rec-body">
          {/* Signal detail */}
          <div className="rec-detail-row">
            <Zap size={14} />
            <span>{rec.signal_detail}</span>
          </div>

          {/* Price grid */}
          <div className="price-grid">
            <div className="price-cell">
              <div className="price-label">Entry Range</div>
              <div className="price-value">${rec.entry_low.toFixed(2)} – ${rec.entry_high.toFixed(2)}</div>
            </div>
            <div className="price-cell">
              <div className="price-label"><Target size={12} /> Target</div>
              <div className="price-value" style={{ color: '#00d97e' }}>${rec.target_price.toFixed(2)}</div>
            </div>
            <div className="price-cell">
              <div className="price-label"><ShieldAlert size={12} /> Stop Loss</div>
              <div className="price-value" style={{ color: '#ff4d6d' }}>${rec.stop_loss.toFixed(2)}</div>
            </div>
            <div className="price-cell">
              <div className="price-label">Risk / Reward</div>
              <div className="price-value">{rec.risk_reward_ratio}</div>
            </div>
          </div>

          {/* Reasoning */}
          <p className="rec-reasoning">{rec.reasoning}</p>

          {/* Robinhood steps */}
          <div className="rh-steps">
            <div className="rh-steps-header">
              <span className="rh-badge">🟢 Robinhood</span>
              <span>Execution Guide</span>
            </div>
            {rec.robinhood_steps.map(s => (
              <div key={s.step} className="rh-step">
                <span className="rh-step-num">{s.step}</span>
                <span>{s.instruction}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Performance Chart ────────────────────────────────────────────────────────

function PerformancePanel({ records }: { records: PerformanceRecord[] }) {
  const outcomes = ['hit_target', 'hit_stop', 'open', 'expired']
  const counts = outcomes.map(o => ({
    name: o.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()),
    value: records.filter(r => r.outcome === o).length,
    color: outcomeColors[o],
  }))

  const winRate = records.length > 0
    ? Math.round((records.filter(r => r.outcome === 'hit_target').length / records.filter(r => r.outcome !== 'open').length) * 100) || 0
    : 0

  const recentPct = records
    .filter(r => r.pct_change !== undefined && r.pct_change !== null)
    .slice(-20)
    .map((r, i) => ({ i, pct: r.pct_change ?? 0, ticker: r.ticker }))

  return (
    <div className="perf-panel">
      <div className="panel-header">
        <BarChart3 size={18} />
        <h3>Performance Tracker</h3>
        <span className="win-rate" style={{ color: winRate >= 50 ? '#00d97e' : '#ff4d6d' }}>
          {winRate}% Win Rate
        </span>
      </div>

      <div className="perf-grid">
        {counts.map(c => (
          <div key={c.name} className="perf-stat">
            <div className="perf-stat-num" style={{ color: c.color }}>{c.value}</div>
            <div className="perf-stat-label">{c.name}</div>
          </div>
        ))}
      </div>

      {recentPct.length > 0 && (
        <div className="chart-wrap">
          <p className="chart-label">Recent Trade Outcomes (%)</p>
          <ResponsiveContainer width="100%" height={100}>
            <BarChart data={recentPct} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <XAxis dataKey="ticker" tick={{ fontSize: 10, fill: '#7b8fa1' }} />
              <YAxis tick={{ fontSize: 10, fill: '#7b8fa1' }} />
              <Tooltip
                formatter={(val: number) => [`${val.toFixed(2)}%`, 'Return']}
                contentStyle={{ background: '#0f1923', border: '1px solid #1e2d3d', borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="pct" radius={[3, 3, 0, 0]}>
                {recentPct.map((entry, i) => (
                  <Cell key={i} fill={entry.pct >= 0 ? '#00d97e' : '#ff4d6d'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {records.length === 0 && (
        <p className="empty-state">No performance data yet. Run your first analysis to start tracking.</p>
      )}
    </div>
  )
}

// ─── Main App ────────────────────────────────────────────────────────────────

export default function App() {
  const { digest, loading, error, refetch } = useLatestDigest()
  const { records } = usePerformance()
  const [triggering, setTriggering] = useState(false)
  const [triggerMsg, setTriggerMsg] = useState('')

  async function handleTrigger() {
    setTriggering(true)
    setTriggerMsg('')
    try {
      const res = await triggerRun()
      setTriggerMsg(res.message)
      setTimeout(refetch, 65000) // re-fetch after 65s
    } catch {
      setTriggerMsg('Failed to trigger run.')
    } finally {
      setTriggering(false)
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <TrendingUp size={22} />
            <span>RobiAgent</span>
          </div>
          <span className="header-sub">AI Trade Intelligence</span>
        </div>
        <div className="header-right">
          {digest && (
            <div className="header-date">
              <Clock size={14} />
              {digest.date}
            </div>
          )}
          <button className="run-btn" onClick={handleTrigger} disabled={triggering}>
            <RefreshCw size={15} className={triggering ? 'spin' : ''} />
            {triggering ? 'Running...' : 'Run Analysis'}
          </button>
        </div>
      </header>

      {triggerMsg && (
        <div className="trigger-banner">{triggerMsg}</div>
      )}

      <main className="main">
        {/* Left column */}
        <div className="left-col">
          {loading && (
            <div className="loading-state">
              <div className="loader" />
              <p>Loading market intelligence...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <AlertTriangle size={20} />
              <p>{error}</p>
            </div>
          )}

          {!loading && !digest && !error && (
            <div className="empty-digest">
              <TrendingUp size={40} opacity={0.3} />
              <h2>No analysis yet</h2>
              <p>Click "Run Analysis" to generate today's trade recommendations.</p>
            </div>
          )}

          {digest && (
            <>
              {/* Market summary */}
              <div className="market-summary">
                <p>{digest.market_summary}</p>
              </div>

              {/* Recommendations */}
              <div className="section-header">
                <h2>Today's Top Picks</h2>
                <span className="count-badge">{digest.recommendations.length} opportunities</span>
              </div>

              <div className="recs-list">
                {digest.recommendations.map(rec => (
                  <RecommendationCard key={rec.ticker} rec={rec} />
                ))}
              </div>

              {/* Disclaimer */}
              <div className="disclaimer">
                <AlertTriangle size={14} />
                <p>{digest.disclaimer}</p>
              </div>
            </>
          )}
        </div>

        {/* Right column */}
        <div className="right-col">
          <PerformancePanel records={records} />
        </div>
      </main>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
          --bg: #080e17;
          --surface: #0f1923;
          --surface2: #162030;
          --border: #1a2940;
          --text: #e8eef4;
          --muted: #7b8fa1;
          --accent: #00d97e;
          --danger: #ff4d6d;
          --warn: #f4a22d;
          --font-display: 'Syne', sans-serif;
          --font-mono: 'DM Mono', monospace;
        }

        body {
          background: var(--bg);
          color: var(--text);
          font-family: var(--font-display);
          min-height: 100vh;
        }

        .app { min-height: 100vh; display: flex; flex-direction: column; }

        /* Header */
        .header {
          display: flex; align-items: center; justify-content: space-between;
          padding: 16px 24px;
          border-bottom: 1px solid var(--border);
          background: var(--surface);
          position: sticky; top: 0; z-index: 100;
        }
        .header-left { display: flex; align-items: center; gap: 16px; }
        .logo {
          display: flex; align-items: center; gap: 8px;
          font-size: 20px; font-weight: 800; color: var(--accent);
          letter-spacing: -0.5px;
        }
        .header-sub { color: var(--muted); font-size: 13px; }
        .header-right { display: flex; align-items: center; gap: 12px; }
        .header-date {
          display: flex; align-items: center; gap: 6px;
          color: var(--muted); font-size: 13px; font-family: var(--font-mono);
        }
        .run-btn {
          display: flex; align-items: center; gap: 7px;
          background: var(--accent); color: #080e17;
          border: none; border-radius: 8px;
          padding: 9px 16px; font-size: 13px; font-weight: 700;
          cursor: pointer; font-family: var(--font-display);
          transition: opacity 0.15s;
        }
        .run-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .run-btn:hover:not(:disabled) { opacity: 0.9; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }

        /* Trigger banner */
        .trigger-banner {
          background: #162030; border-bottom: 1px solid var(--border);
          padding: 10px 24px; font-size: 13px; color: var(--warn);
          font-family: var(--font-mono);
        }

        /* Main layout */
        .main {
          flex: 1; display: grid;
          grid-template-columns: 1fr 340px;
          gap: 24px; padding: 24px;
          max-width: 1280px; margin: 0 auto; width: 100%;
        }

        /* States */
        .loading-state, .error-state, .empty-digest {
          display: flex; flex-direction: column; align-items: center;
          justify-content: center; gap: 12px;
          padding: 60px; color: var(--muted); text-align: center;
        }
        .loader {
          width: 36px; height: 36px; border-radius: 50%;
          border: 3px solid var(--border); border-top-color: var(--accent);
          animation: spin 0.8s linear infinite;
        }
        .empty-digest h2 { font-size: 20px; color: var(--text); }
        .empty-digest p { font-size: 14px; max-width: 280px; }
        .error-state { color: var(--danger); }

        /* Market summary */
        .market-summary {
          background: linear-gradient(135deg, #0f2318, #0f1923);
          border: 1px solid #1a3d26;
          border-radius: 12px; padding: 16px 20px;
          margin-bottom: 20px; color: #a8d5bb;
          font-size: 14px; line-height: 1.6;
        }

        /* Section header */
        .section-header {
          display: flex; align-items: center; justify-content: space-between;
          margin-bottom: 14px;
        }
        .section-header h2 { font-size: 18px; font-weight: 700; }
        .count-badge {
          background: var(--surface2); color: var(--muted);
          padding: 4px 10px; border-radius: 20px; font-size: 12px;
          border: 1px solid var(--border);
        }

        /* Recs list */
        .recs-list { display: flex; flex-direction: column; gap: 12px; }

        /* Rec card */
        .rec-card {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 12px; overflow: hidden;
          transition: border-color 0.15s;
        }
        .rec-card:hover { border-color: #2a3f5a; }
        .rec-header {
          display: flex; align-items: center; justify-content: space-between;
          padding: 16px 18px; cursor: pointer; gap: 12px;
        }
        .rec-left { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
        .rec-ticker {
          font-family: var(--font-mono); font-size: 16px; font-weight: 500;
          color: var(--text); flex-shrink: 0;
        }
        .rec-company {
          font-size: 13px; color: var(--muted);
          overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }
        .rec-signal {
          display: flex; align-items: center; gap: 5px;
          font-size: 12px; font-weight: 600; border: 1px solid;
          padding: 3px 9px; border-radius: 20px; flex-shrink: 0;
        }
        .rec-right { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
        .rec-price { font-family: var(--font-mono); font-size: 15px; }
        .rec-target { font-family: var(--font-mono); font-size: 14px; font-weight: 600; }
        .rec-conf {
          font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px;
          text-transform: uppercase; letter-spacing: 0.5px;
        }

        /* Rec body */
        .rec-body { padding: 0 18px 18px; border-top: 1px solid var(--border); }
        .rec-detail-row {
          display: flex; align-items: center; gap: 8px;
          padding: 12px 0; color: var(--muted); font-size: 13px;
          border-bottom: 1px solid var(--border);
        }
        .price-grid {
          display: grid; grid-template-columns: 1fr 1fr 1fr 1fr;
          gap: 12px; padding: 14px 0;
        }
        .price-cell { display: flex; flex-direction: column; gap: 4px; }
        .price-label {
          display: flex; align-items: center; gap: 4px;
          color: var(--muted); font-size: 11px; text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .price-value { font-family: var(--font-mono); font-size: 14px; font-weight: 500; }
        .rec-reasoning {
          font-size: 13px; line-height: 1.65; color: #9fb4c7;
          padding: 0 0 14px; border-bottom: 1px solid var(--border);
        }

        /* Robinhood steps */
        .rh-steps { padding-top: 14px; }
        .rh-steps-header {
          display: flex; align-items: center; gap: 10px;
          margin-bottom: 12px; font-size: 13px; font-weight: 600;
        }
        .rh-badge {
          background: #0a2010; border: 1px solid #0d4020;
          color: var(--accent); padding: 3px 8px; border-radius: 6px;
          font-size: 12px;
        }
        .rh-step {
          display: flex; align-items: flex-start; gap: 12px;
          padding: 8px 0; font-size: 13px; color: #9fb4c7;
          border-bottom: 1px solid #10202e;
        }
        .rh-step:last-child { border-bottom: none; }
        .rh-step-num {
          background: var(--surface2); color: var(--accent);
          border: 1px solid #1a3d26; border-radius: 50%;
          width: 22px; height: 22px; display: flex; align-items: center;
          justify-content: center; font-size: 11px; font-weight: 700;
          flex-shrink: 0; font-family: var(--font-mono);
        }

        /* Disclaimer */
        .disclaimer {
          display: flex; align-items: flex-start; gap: 10px;
          background: #1a0f0a; border: 1px solid #3d1f10;
          border-radius: 10px; padding: 14px 16px; margin-top: 20px;
          color: #a07060; font-size: 12px; line-height: 1.6;
        }
        .disclaimer svg { flex-shrink: 0; margin-top: 1px; }

        /* Performance panel */
        .perf-panel {
          background: var(--surface); border: 1px solid var(--border);
          border-radius: 14px; padding: 20px; position: sticky; top: 80px;
        }
        .panel-header {
          display: flex; align-items: center; gap: 10px; margin-bottom: 18px;
        }
        .panel-header h3 { font-size: 15px; font-weight: 700; flex: 1; }
        .win-rate { font-family: var(--font-mono); font-size: 14px; font-weight: 600; }
        .perf-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 18px; }
        .perf-stat {
          background: var(--surface2); border: 1px solid var(--border);
          border-radius: 10px; padding: 12px; text-align: center;
        }
        .perf-stat-num { font-size: 24px; font-weight: 800; font-family: var(--font-mono); }
        .perf-stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
        .chart-wrap { margin-top: 16px; }
        .chart-label { font-size: 11px; color: var(--muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        .empty-state { font-size: 13px; color: var(--muted); text-align: center; padding: 20px 0; line-height: 1.6; }

        /* Mobile */
        @media (max-width: 768px) {
          .main { grid-template-columns: 1fr; padding: 16px; }
          .right-col { order: -1; }
          .perf-panel { position: static; }
          .price-grid { grid-template-columns: 1fr 1fr; }
          .rec-company { display: none; }
          .header-sub { display: none; }
        }
      `}</style>
    </div>
  )
}
