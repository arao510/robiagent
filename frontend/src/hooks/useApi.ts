import { useState, useEffect, useCallback } from 'react'
import type { DailyDigest, PerformanceRecord } from '../types'

const BASE = '/api'

export function useLatestDigest() {
  const [digest, setDigest] = useState<DailyDigest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch_ = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/digest/latest`)
      if (res.status === 404) {
        setDigest(null)
      } else if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      } else {
        setDigest(await res.json())
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetch_() }, [fetch_])
  return { digest, loading, error, refetch: fetch_ }
}

export function useDigestHistory() {
  const [history, setHistory] = useState<DailyDigest[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${BASE}/digest/history`)
      .then(r => r.json())
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false))
  }, [])

  return { history, loading }
}

export function usePerformance() {
  const [records, setRecords] = useState<PerformanceRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${BASE}/performance`)
      .then(r => r.json())
      .then(setRecords)
      .catch(() => setRecords([]))
      .finally(() => setLoading(false))
  }, [])

  return { records, loading }
}

export async function triggerRun(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${BASE}/run`, { method: 'POST' })
  return res.json()
}
