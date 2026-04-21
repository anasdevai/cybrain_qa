import React, { useState } from 'react'
import { Search, ArrowRight, Sparkles } from 'lucide-react'
import './DashboardComponents.css'

const CHIPS_ROW1 = [
  'Welche SOPs haben die meisten Abweichungen?',
  'Fasse die letzten Audit-Findings zusammen',
  'Was sind offene CAPA Maßnahmen?',
]

const CHIPS_ROW2 = [
  'Gibt es Risiken bei Reinigungsvalidierung?',
  'Welche SOP sollte dringend überprüft werden?',
]

export default function AISearchSection({ onSubmit, loading }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim() && !loading) onSubmit(query.trim())
  }

  const handleChipClick = (text) => {
    if (loading) return
    setQuery(text)
    onSubmit(text)
  }

  return (
    <section className="ai-search-card" aria-label="KI-gestütztes Qualitätswesen">
      {/* Header tag */}
      <div className="ai-search-header-tag">
        <span className="ai-search-tag-arrow"><ArrowRight size={11} /></span>
        <span className="ai-search-tag-text">KI-gestütztes Qualitätswesen</span>
      </div>

      {/* Title block */}
      <div className="ai-search-title-block">
        <h2 className="ai-search-title">Was möchten Sie über Ihr Qualitätswissen wissen?</h2>

        <div className="ai-search-ki-row">
          <span className="ai-ki-icon-wrap"><Sparkles size={13} /></span>
          <span className="ai-ki-label">KI fragen</span>
        </div>

        <p className="ai-search-description">
          Stellen Sie eine Frage in natürlicher Sprache — die KI durchsucht SOPs, Abweichungen,
          CAPAs und Audits und liefert eine Zusammenfassung mit Quellenangaben.
        </p>
      </div>

      {/* Search input */}
      <form className="ai-search-input-box" onSubmit={handleSubmit}>
        <input
          type="text"
          className="ai-search-input"
          placeholder="z.B. Welche SOPs sind besonders risikoreich? Was waren die Hauptursachen der Abweichungen in Q1?"
          value={query}
          onChange={e => setQuery(e.target.value)}
          disabled={loading}
          aria-label="KI-Suchanfrage"
        />
        <button
          type="submit"
          className={`ai-kontext-btn${loading ? ' loading' : ''}`}
          disabled={loading || !query.trim()}
          aria-label="Kontext analysieren"
        >
          {loading ? (
            <span className="ai-spinner" />
          ) : (
            <>
              <Search size={12} />
              <span>Kontext analysieren</span>
            </>
          )}
        </button>
      </form>

      {/* Suggestion chips */}
      <div className="ai-chips-section">
        <div className="ai-chips-row">
          {CHIPS_ROW1.map(chip => (
            <button
              key={chip}
              type="button"
              className="ai-chip"
              onClick={() => handleChipClick(chip)}
              disabled={loading}
            >
              {chip}
            </button>
          ))}
        </div>
        <div className="ai-chips-row">
          {CHIPS_ROW2.map(chip => (
            <button
              key={chip}
              type="button"
              className="ai-chip"
              onClick={() => handleChipClick(chip)}
              disabled={loading}
            >
              {chip}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
