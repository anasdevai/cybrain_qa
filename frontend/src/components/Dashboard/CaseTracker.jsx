import React from 'react'
import { Plus, TrendingUp } from 'lucide-react'
import './DashboardComponents.css'
import StatusBadge from '../Common/StatusBadge'



/** Dot color based on impact/type */
function getDotColor(item) {
  if (item.type === 'deviation') {
    const impact = (item.impact_level || '').toLowerCase()
    if (impact.includes('critical') || impact.includes('high')) return '#c43d1b'
    if (impact.includes('medium')) return '#d4933a'
    return '#3c5dcb'
  }
  if (item.type === 'capa') return '#d4933a'
  if (item.type === 'audit') return '#6d28d9'
  if (item.type === 'decision') return '#0891b2'
  return '#d9d9d9'
}

function CaseSkeleton() {
  return (
    <div className="case-skeleton">
      {[1, 2, 3].map(i => (
        <div key={i} className="case-skeleton-row">
          <div className="shimmer-circle" />
          <div className="shimmer-line" />
          <div className="shimmer-badge" />
        </div>
      ))}
    </div>
  )
}

export default function CaseTracker({ cases = [], loading = false }) {
  return (
    <div className="dash-card" aria-label="Aktuelle Fälle">
      {/* Card header */}
      <div className="dash-card-header">
        <h3 className="dash-card-title">Aktuelle Fälle &amp; relevante Situationen</h3>
        <button className="dash-view-all-btn" aria-label="Alle Fälle anzeigen">
          Alle anzeigen →
        </button>
      </div>

      {loading && <CaseSkeleton />}

      {!loading && cases.length === 0 && (
        <p className="dash-empty-state">Keine aktuellen Fälle gefunden.</p>
      )}

      {!loading && cases.length > 0 && (
        <div className="cases-list">
          {cases.map((item, idx) => {
            const dotColor = getDotColor(item)
            const isFirst = idx === 0

            return (
              <React.Fragment key={item.id}>
                <div className={`case-row${isFirst ? ' case-row-expanded' : ''}`}>
                  <div className="case-main-line">
                    <span
                      className="case-dot"
                      style={{ backgroundColor: dotColor }}
                      aria-hidden="true"
                    />
                    <div className="case-info">
                      <span className="case-number">{item.id}</span>
                      <span className="case-title-text">{item.title}</span>
                    </div>
                    <StatusBadge status={item.status || (item.type === 'deviation' ? 'Offen' : 'Aktiv')} />
                  </div>
                  {isFirst && (
                    <div className="case-expanded-body">
                      <div className="case-action-row">
                        <button className="case-action-btn kontext" aria-label="Kontext anzeigen">
                          <Plus size={10} />
                          <span>Kontext anzeigen</span>
                        </button>
                        <button className="case-action-btn analyse" aria-label="Analysieren">
                          <TrendingUp size={10} />
                          <span>Analysieren</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {idx < cases.length - 1 && (
                  <div className="case-divider" aria-hidden="true" />
                )}
              </React.Fragment>
            )
          })}
        </div>
      )}
    </div>
  )
}
