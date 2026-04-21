import React from 'react'
import { FileSearch, ClipboardCheck, AlertTriangle, BookOpen } from 'lucide-react'
import './DashboardComponents.css'
import StatusBadge from '../Common/StatusBadge'

const QUICK_ACCESS = [
  { icon: <FileSearch size={20} />, label: 'SOP durchsuchen', sub: 'Volltext & Kontext', colorClass: 'qa-green' },
  { icon: <AlertTriangle size={20} />, label: 'Abweichungen', sub: 'Analysieren & prüfen', colorClass: 'qa-orange' },
  { icon: <ClipboardCheck size={20} />, label: 'CAPA verwalten', sub: 'Maßnahmen & Status', colorClass: 'qa-green' },
  { icon: <BookOpen size={20} />, label: 'Audit-Bezug', sub: 'Findings & Bezüge', colorClass: 'qa-blue' },
]



function SOPSkeleton() {
  return (
    <div className="sop-skeleton">
      {[1, 2, 3].map(i => (
        <div key={i} className="sop-skeleton-row">
          <div className="shimmer-line long" />
          <div className="shimmer-badge" />
        </div>
      ))}
    </div>
  )
}

export default function RelevantSOPs({ sops = [], loading = false }) {
  const featuredSOP = sops[0] || null
  const gridSOPs = sops.slice(1, 3)

  return (
    <div className="dash-card" aria-label="Relevante SOPs">
      {/* Card header */}
      <div className="dash-card-header">
        <h3 className="dash-card-title">Relevante SOPs im aktuellen Kontext</h3>
      </div>

      <div className="sop-divider" />

      {loading && <SOPSkeleton />}

      {!loading && sops.length === 0 && (
        <p className="dash-empty-state">Keine SOPs gefunden.</p>
      )}

      {!loading && sops.length > 0 && (
        <>
          {/* Featured SOP */}
          {featuredSOP && (
            <div className="sop-featured-card">
              <div className="sop-featured-header">
                <span className="sop-number-text">
                  {featuredSOP.metadata_json?.sop_number || featuredSOP.title?.slice(0, 10) || 'SOP'}
                </span>
                <StatusBadge status={featuredSOP.status || 'Active'} />
              </div>
              <p className="sop-desc">{featuredSOP.title}</p>
              {featuredSOP.version_number && (
                <p className="sop-version">Version {featuredSOP.version_number}</p>
              )}
            </div>
          )}

          {/* Two-column grid SOPs */}
          {gridSOPs.length > 0 && (
            <div className="sop-grid-two">
              {gridSOPs.map((sop, i) => (
                <div key={sop.id || i} className="sop-mini-card">
                  <div className="sop-mini-header">
                    <span className="sop-number-text small">
                      {sop.metadata_json?.sop_number || sop.title?.slice(0, 8) || 'SOP'}
                    </span>
                    <StatusBadge status={sop.status || 'Active'} />
                  </div>
                  <p className="sop-mini-desc">{sop.title}</p>
                  {sop.version_number && (
                    <p className="sop-version">v{sop.version_number}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      <div className="sop-divider" />

      {/* Direkter Zugriff — always shown */}
      <div className="sop-quick-access">
        <p className="sop-quick-title">Direkter Zugriff auf Qualitätswissen</p>
        <div className="sop-quick-grid">
          {QUICK_ACCESS.map(item => (
            <button key={item.label} className={`sop-quick-btn ${item.colorClass}`} aria-label={item.label}>
              <span className="sop-quick-icon">{item.icon}</span>
              <div className="sop-quick-text">
                <span className="sop-quick-label">{item.label}</span>
                <span className="sop-quick-sub">{item.sub}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
