import { useState, useEffect } from 'react'
import { getSOPs, getDeviations } from '../api/editorApi'

/**
 * Fetches real-time counts for SOPs and Deviations from the backend.
 * Returns { sopCount, deviationCount } — both default to null while loading.
 * On error, returns 0 so the badge shows 0 rather than stale fake data.
 */
export function useSidebarCounts() {
  const [sopCount, setSopCount] = useState(null)
  const [deviationCount, setDeviationCount] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function fetchCounts() {
      try {
        const [sops, devs] = await Promise.all([
          getSOPs().catch(() => []),
          getDeviations().catch(() => []),
        ])
        if (cancelled) return
        setSopCount(Array.isArray(sops) ? sops.length : 0)
        setDeviationCount(Array.isArray(devs) ? devs.length : 0)
      } catch {
        if (!cancelled) {
          setSopCount(0)
          setDeviationCount(0)
        }
      }
    }

    fetchCounts()

    // Refresh every 60 seconds so the badges stay current
    const interval = setInterval(fetchCounts, 60_000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  return { sopCount, deviationCount }
}
