import React from 'react'
import { CheckCircle2, Download, MessageSquare, BookmarkPlus, ExternalLink } from 'lucide-react'
import './DashboardComponents.css'

/** Returns source display config based on type */
function getSourceConfig(type) {
  switch ((type || '').toLowerCase()) {
    case 'sop':      return { icon: '📄', colorClass: 'source-sop' }
    case 'deviation': return { icon: '⚠',  colorClass: 'source-warning' }
    case 'capa':     return { icon: '◆',  colorClass: 'source-warning' }
    case 'audit':    return { icon: '✓',  colorClass: 'source-audit' }
    default:         return { icon: '•',  colorClass: 'source-sop' }
  }
}

/** Format timestamp as "vor X Min." */
function formatTimestamp(ts) {
  if (!ts) return ''
  const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 60000)
  if (diff < 1) return 'Gerade eben'
  if (diff === 1) return 'vor 1 Min.'
  if (diff < 60) return `vor ${diff} Min.`
  const hrs = Math.floor(diff / 60)
  return `vor ${hrs} Std.`
}

export default function AISummaryCard({ query, response, sources = [], timestamp, loading, error }) {
  // Don't render if nothing to show
  if (!query && !loading && !error) return null

  const actions = [
    { label: 'Exportieren', icon: <Download size={11} />, primary: true },
    { label: 'Weiter fragen', icon: null, primary: false },
    { label: 'Notiz speichern', icon: null, primary: false },
    { label: 'SOPs öffnen', icon: null, primary: false },
  ]

  return (
    <div className="ai-summary-wrapper">
      {/* Header row — outside the card */}
      <div className="ai-summary-header-row">
        <div className="ai-summary-header-left">
          <span className="ai-summary-check-icon" aria-hidden="true">
            <CheckCircle2 size={14} strokeWidth={2.5} />
          </span>
          <span className="ai-summary-label">KI-Zusammenfassung</span>
          {query && (
            <span className="ai-summary-query-text">
              „{query}"
            </span>
          )}
        </div>
        {timestamp && !loading && (
          <span className="ai-summary-timestamp">{formatTimestamp(timestamp)}</span>
        )}
      </div>

      {/* Card body */}
      <div className="ai-summary-card">
        {loading && (
          <div className="ai-summary-loading" role="status" aria-label="KI lädt…">
            <div className="shimmer" />
            <div className="shimmer" />
            <div className="shimmer short" />
          </div>
        )}

        {error && !loading && (
          <p className="ai-summary-error">{error}</p>
        )}

        {response && !loading && (
          <>
            <p className="ai-summary-body">{response}</p>

            {/* Sources */}
            {sources.length > 0 && (
              <div className="ai-sources-block">
                <span className="ai-sources-label">Quellen dieser Antwort</span>
                <div className="ai-sources-list">
                  {sources.map((s, i) => {
                    const cfg = getSourceConfig(s.type)
                    return (
                      <span key={i} className={`ai-source-chip ${cfg.colorClass}`}>
                        {cfg.icon} {s.label}
                      </span>
                    )
                  })}
                </div>
              </div>
            )}

            <div className="ai-summary-divider" />

            {/* Actions */}
            <div className="ai-summary-actions">
              {actions.map(a => (
                <button key={a.label} className={`ai-action-btn${a.primary ? ' primary' : ''}`}>
                  {a.icon && a.icon}
                  {a.label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
