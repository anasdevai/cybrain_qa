import React, { useState, useCallback, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, ArrowRight, CheckCircle2, Download,
  ExternalLink, Eye, FileText, Network, AlertTriangle, HelpCircle
} from 'lucide-react'
import { getKnowledgeStats, searchKnowledge } from '../api/editorApi'
import './KnowledgePage.css'

// ── Badge color mapping for result type ───────────────────────
const TYPE_CONFIG = {
  sop: { borderColor: 'var(--primary)', bgColor: '#dcfce7', textColor: 'var(--primary)' },
  deviation: { borderColor: 'var(--status-urgent)', bgColor: '#fdf0ed', textColor: 'var(--status-urgent)' },
  capa: { borderColor: 'var(--status-review)', bgColor: '#fdf6ed', textColor: 'var(--status-review)' },
  audit: { borderColor: 'var(--status-released)', bgColor: '#eef0fb', textColor: 'var(--status-released)' },
  decision: { borderColor: '#6b7280', bgColor: '#f3f4f6', textColor: '#374151' },
}

// ── Timestamp formatter ───────────────────────────────────────
function formatTimestamp(ts) {
  if (!ts) return ''
  const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 60000)
  if (diff < 1) return 'Gerade eben'
  if (diff === 1) return 'vor 1 Min.'
  if (diff < 60) return `vor ${diff} Min.`
  return `vor ${Math.floor(diff / 60)} Std.`
}

// ═══════════════════════════════════════════════════════════════
// KnowledgeResultCard
// ═══════════════════════════════════════════════════════════════
function KnowledgeResultCard({ result, onOpen }) {
  const cfg = TYPE_CONFIG[result.type] || TYPE_CONFIG.sop

  return (
    <div className="ws-result-card" style={{ borderLeftColor: cfg.borderColor }}>
      {/* Header row */}
      <div className="ws-result-header">
        <div className="ws-result-type-row">
          <span
            className="ws-result-type-icon"
            style={{ borderColor: cfg.borderColor, color: cfg.borderColor }}
            aria-hidden="true"
          >
            {result.type === 'sop' && <FileText size={9} />}
            {result.type === 'deviation' && <span className="ws-type-symbol">⚠</span>}
            {result.type === 'capa' && <CheckCircle2 size={8} />}
            {result.type === 'audit' && <span className="ws-type-symbol">☐</span>}
            {result.type === 'decision' && <HelpCircle size={9} />}
          </span>
          <span className="ws-result-type-badge" style={{ color: cfg.textColor }}>
            {result.typeLabel}
          </span>
          <span className="ws-result-metadata">{result.metadata}</span>
        </div>
        <span className="ws-result-match" style={{ color: cfg.textColor }}>
          {result.matchPercent}% Übereinstimmung
        </span>
      </div>

      {/* Content + actions */}
      <div className="ws-result-body">
        <div className="ws-result-content">
          <h4 className="ws-result-title">{result.title}</h4>
          <p className="ws-result-excerpt">{result.excerpt}</p>
          <div className="ws-result-badges">
            {result.badges.filter(b => b && b.label).map(b => (
              <span key={b.label} className={`ws-badge ws-badge-${b.color || 'gray'}`}>
                {b.label}
              </span>
            ))}
          </div>
        </div>
        <div className="ws-result-actions">
          <button className="ws-action-btn ws-action-open" aria-label={`${result.title} öffnen`} onClick={() => onOpen(result)}>
            <Eye size={12} />
            <span>Öffnen</span>
          </button>
          <button className="ws-action-btn ws-action-context" aria-label={`${result.title} Kontext`} onClick={() => onOpen(result)}>
            <Network size={10} />
            <span>Kontext</span>
          </button>
        </div>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
// KnowledgePage
// ═══════════════════════════════════════════════════════════════
export default function KnowledgePage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)

  const [stats, setStats] = useState({ sops: 0, deviations: 0, capas: 0, audits: 0, decisions: 0 })

  // Results state
  const [showResults, setShowResults] = useState(false)
  const [results, setResults] = useState([])
  const [summary, setSummary] = useState(null)

  // Fetch real count stats on mount
  useEffect(() => {
    async function loadStats() {
      setInitialLoading(true)
      try {
        const counts = await getKnowledgeStats()
        setStats(counts)
      } catch (err) {
        console.error('Failed to load knowledge metrics', err)
      } finally {
        setInitialLoading(false)
      }
    }
    loadStats()
  }, [])

  // Dynamic tags
  const sourceTags = useMemo(() => [
    { label: `SOPs · ${stats.sops}`, colorClass: 'tag-sop' },
    { label: `Abweichungen · ${stats.deviations}`, colorClass: 'tag-deviation' },
    { label: `CAPAs · ${stats.capas}`, colorClass: 'tag-capa' },
    { label: `Audits · ${stats.audits}`, colorClass: 'tag-audit' },
    { label: `Entscheidungen · ${stats.decisions}`, colorClass: 'tag-decision' },
  ], [stats])

  // Chips
  const CHIPS_ROW1 = [
    'Welche SOPs haben die meisten Abweichungen?',
    'Zeige mir ungelöste CAPAs',
    'Zusammenfassung der letzten Audits',
  ]
  const CHIPS_ROW2 = [
    'Risiken bei Validierung',
    'Kürzlich aktualisierte Dokumente',
  ]

  const handleSubmit = useCallback(async (text) => {
    const trimmed = (text || query).trim()
    if (!trimmed || loading || initialLoading) return
    setQuery(text)
    setLoading(true)
    setShowResults(false)

    try {
      const matched = await searchKnowledge(trimmed)

      // Build dynamic summary based on results
      let summaryText = 'Ihre Suche ergab keine direkten Treffer in der Datenbank. Versuchen Sie, andere Suchbegriffe zu verwenden.'
      let summarySources = []

      if (matched.length > 0) {
        summaryText = `Es wurden ${matched.length} Dokumente im Zusammenhang mit Ihrer Anfrage "${trimmed}" gefunden. `

        const topSops = matched.filter(m => m.type === 'sop')
        const topDevs = matched.filter(m => m.type === 'deviation')

        if (topSops.length > 0) {
          summaryText += `Besonders relevant ist die SOP ${topSops[0].title}. `
        }
        if (topDevs.length > 0) {
          summaryText += `Es gibt ${topDevs.length} verknüpfte Abweichung(en), z.B. ${topDevs[0].title}, welche beachtet werden sollten. `
        }
        summaryText += 'Die vollständige Liste der Dokumente und deren Kontext finden Sie in den Treffern.'

        summarySources = matched.slice(0, 6).map(m => ({
          icon: m.sourceIcon,
          label: m.title.substring(0, 20) + (m.title.length > 20 ? '...' : ''),
          colorClass: m.sourceColorClass
        }))
      }

      setResults(matched)
      setSummary({
        query: text || query,
        text: summaryText,
        sources: summarySources,
        timestamp: new Date()
      })
    } catch (err) {
      console.error("Search failed", err)
      setResults([])
      setSummary({
        query: text || query,
        text: "Fehler beim Laden der Suchergebnisse aus dem Backend.",
        sources: [],
        timestamp: new Date()
      })
    } finally {
      setLoading(false)
      setShowResults(true)
    }
  }, [loading, initialLoading, query])

  const handleFormSubmit = (e) => {
    e.preventDefault()
    handleSubmit(query)
  }

  const handleChipClick = (chip) => {
    if (loading || initialLoading) return
    setQuery(chip)
    handleSubmit(chip)
  }

  const handleOpenItem = (item) => {
    if (item.type === 'sop') {
      navigate(`/editor/${item.id}`)
    } else {
      // For deviations, capas, audits we navigate to their respective listing pages
      navigate(`/${item.type}s`)
    }
  }

  const summaryActions = [
    { label: 'Exportieren', primary: true },
    { label: 'Weiter fragen', primary: false },
    { label: 'Notiz speichern', primary: false },
    { label: 'SOPs öffnen', primary: false },
  ]

  return (
    <div className="ws-page">
      {/* ── Search Section ── */}
      <section className="ws-search-card" aria-label="Wissenssuche">
        <div className="ws-header-tag">
          <span className="ws-tag-arrow"><ArrowRight size={11} /></span>
          <span className="ws-tag-text">Wissenssuche</span>
        </div>

        <div className="ws-title-block">
          <h2 className="ws-title">Was möchten Sie in Ihrem Qualitätswissen finden?</h2>
          <p className="ws-description">
            Stellen Sie eine Frage oder geben Sie einen Begriff ein — die KI durchsucht SOPs,
            Abweichungen, CAPAs, Audit-Findings und Entscheidungen gleichzeitig und liefert
            eine Zusammenfassung auf Basis Ihrer echten Daten.
          </p>
        </div>

        <form className="ws-search-input-box" onSubmit={handleFormSubmit}>
          <input
            type="text"
            className="ws-search-input"
            placeholder="z.B. Zeige mir alle offenen Abweichungen..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            disabled={loading || initialLoading}
            aria-label="Wissenssuche Anfrage"
          />
          <button
            type="submit"
            className={`ws-kontext-btn${loading ? ' loading' : ''}`}
            disabled={loading || initialLoading || !query.trim()}
            aria-label="Kontext analysieren"
          >
            {loading ? (
              <span className="ws-spinner" />
            ) : (
              <>
                <Search size={12} />
                <span>Kontext analysieren</span>
              </>
            )}
          </button>
        </form>

        <div className="ws-sources-section">
          <span className="ws-sources-label">Echte Backend Quellen:</span>
          {initialLoading ? (
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Synchronisiere Daten...</span>
          ) : (
            <div className="ws-source-tags">
              {sourceTags.map(t => (
                <span key={t.label} className={`ws-source-tag ${t.colorClass}`}>
                  {t.label}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="ws-chips-section">
          <div className="ws-chips-row">
            {CHIPS_ROW1.map(chip => (
              <button key={chip} type="button" className="ws-chip" onClick={() => handleChipClick(chip)} disabled={loading || initialLoading}>
                {chip}
              </button>
            ))}
          </div>
          <div className="ws-chips-row">
            {CHIPS_ROW2.map(chip => (
              <button key={chip} type="button" className="ws-chip" onClick={() => handleChipClick(chip)} disabled={loading || initialLoading}>
                {chip}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── KI-Zusammenfassung ── */}
      {showResults && summary && (
        <>
          <div className="ws-summary-wrapper">
            <div className="ws-summary-header-row">
              <div className="ws-summary-header-left">
                <span className="ws-summary-check"><CheckCircle2 size={14} strokeWidth={2.5} /></span>
                <span className="ws-summary-label">Generierte Zusammenfassung</span>
                <span className="ws-summary-query">„{summary.query}"</span>
              </div>
              <span className="ws-summary-time">{formatTimestamp(summary.timestamp)}</span>
            </div>

            <div className="ws-summary-card">
              <p className="ws-summary-body">{summary.text}</p>

              {summary.sources.length > 0 && (
                <div className="ws-summary-sources">
                  <span className="ws-summary-sources-label">Gefundene Referenzen:</span>
                  <div className="ws-summary-sources-list">
                    {summary.sources.map((s, i) => (
                      <span key={i} className={`ws-summary-source-chip ${s.colorClass}`}>
                        {s.icon} {s.label}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="ws-summary-divider" />

              <div className="ws-summary-actions">
                {summaryActions.map(a => (
                  <button key={a.label} className={`ws-summary-action-btn${a.primary ? ' primary' : ''}`}>
                    {a.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* ── Relevante Wissenstreffer ── */}
          <section className="ws-results-section" aria-label="Relevante Wissenstreffer">
            <h3 className="ws-results-title">Relevante Backend-Treffer ({results.length})</h3>

            {results.length === 0 ? (
              <div style={{ padding: '24px 0', color: 'var(--text-muted)' }}>
                Keine passenden Datensätze gefunden.
              </div>
            ) : (
              <div className="ws-results-list">
                {results.map(r => (
                  <KnowledgeResultCard key={`${r.type}-${r.id}`} result={r} onOpen={handleOpenItem} />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}
