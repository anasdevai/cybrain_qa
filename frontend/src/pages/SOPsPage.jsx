import React, { useState, useEffect, useCallback } from 'react'
import {
  Search, Plus, ChevronDown, ChevronUp, ArrowLeft,
  Sparkles, ExternalLink, Edit3, Filter, Download,
  AlertCircle, FileText, X, FileEdit, List, Loader
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { getSOPs, queryAI } from '../api/editorApi'
import SOPTable from '../components/SOPs/SOPTable'
import StatusBadge from '../components/Common/StatusBadge'
import EditorPage from './EditorPage'
import './SOPsPage.css'

// ── Quick filter suggestions (UI labels only — not mock data) ──────────────
const quickFilters = [
  'Welche SOPs haben die meisten Abweichungen?',
  'Welche SOP wird am häufigsten verletzt?',
  'Was sind meine kritischen CAPA-Maßnahmen?',
  'Führe mir die Audit-Findings zusammen',
]

// ── Sub-components ─────────────────────────────────────────────────────────

function CategoryBadge({ category }) {
  return <span className="sop-cat-badge sop-cat-blue">{category || 'Quality'}</span>
}

function SOPCard({ sop, onOpen, onOpenNewTab, onEdit }) {
  return (
    <div className="sop-context-card">
      <div className="sop-card-header">
        <span className="sop-card-code">{sop.sop_number}</span>
        <StatusBadge status={sop.status} />
      </div>
      <h3 className="sop-card-title">{sop.title}</h3>
      {sop.department && (
        <p className="sop-card-desc">{sop.department}</p>
      )}

      <div className="sop-card-meta">
        <CategoryBadge category={sop.department} />
        {sop.version_number && (
          <span className="sop-card-meta-pill sop-meta-muted">
            v{sop.version_number}
          </span>
        )}
      </div>

      <div className="sop-card-actions">
        <button className="sop-card-btn sop-card-btn-primary" onClick={() => onOpen(sop)}>
          Öffnen
        </button>
        <button 
          className="sop-card-btn sop-card-btn-ghost" 
          onClick={() => onOpenNewTab(sop)}
          title="In neuem Tab öffnen"
        >
          <ExternalLink size={13} />
        </button>
        <button className="sop-card-btn sop-card-btn-ghost" onClick={() => onEdit(sop)}>
          <Edit3 size={13} /> Bearbeiten
        </button>
      </div>
    </div>
  )
}

function KISummary({ open, onToggle, query, summaryText, sources, loading, error }) {
  return (
    <div className={`sops-ki-summary ${open ? 'sops-ki-open' : ''}`}>
      <button className="ki-summary-header" onClick={onToggle}>
        <div className="ki-header-left">
          <Sparkles size={14} className="ki-sparkle" />
          <span className="ki-title">KI-Zusammenfassung</span>
          <span className="ki-subtitle">„{query || 'Welche SOPs haben die meisten Abweichungen?'}"</span>
        </div>
        <div className="ki-header-right">
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {open && (
        <div className="ki-summary-body">
          {loading ? <p className="ki-summary-text">KI analysiert Kontext...</p> : null}
          {error ? <p className="ki-summary-text" style={{ color: 'var(--error)' }}>{error}</p> : null}
          {!loading && !error ? (
            <p className="ki-summary-text" style={{ color: 'var(--text-muted)', fontSize: 13 }}>
              {summaryText || 'Frage stellen, um eine KI-Zusammenfassung aus dem Backend zu laden.'}
            </p>
          ) : null}
          {!loading && sources?.length > 0 ? (
            <div className="ki-summary-source-list">
              {sources.slice(0, 5).map((src, idx) => (
                <span key={`${src?.id || src?.label || 'src'}-${idx}`} className="ki-summary-source-chip">
                  {src?.label || src?.id || `Quelle ${idx + 1}`}
                </span>
              ))}
            </div>
          ) : null}
          <div className="ki-summary-actions">
            <button className="ki-action-btn">
              <Download size={13} /> Exportieren
            </button>
            <button className="ki-action-btn">Weitere Fragen</button>
            <button className="ki-action-btn ki-action-primary">SOPs öffnen</button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Map raw /api/sops record into a display-ready shape ───────────────────
function mapSOP(s) {
  const cv = s.current_version
  return {
    id: String(s.id),
    sop_number: s.sop_number || String(s.id).slice(0, 8),
    title: s.title || 'Untitled',
    department: s.department || '',
    version_number: cv?.version_number || '1',
    status: cv?.external_status || 'draft',
    // For the table view
    code: s.sop_number || String(s.id).slice(0, 8),
    version: cv?.version_number ? `V ${cv.version_number}` : 'V 1',
    date: s.updated_at ? new Date(s.updated_at).toLocaleDateString('de-DE') : '—',
    owner: cv?.metadata_json?.sopMetadata?.author || s.department || 'System',
    is_active: s.is_active,
    updated_at_raw: s.updated_at || null, // kept for client-side sorting
  }
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function SOPsPage() {
  const navigate = useNavigate()
  // ── Document tab system ──────────────────────────────────────────────────
  const [tabs, setTabs] = useState([
    { id: 'sops-list', label: 'SOPs', type: 'list', closeable: false },
  ])
  const [activeTabId, setActiveTabId] = useState('sops-list')

  const openNewSOPTab = useCallback(() => {
    const tabId = 'editor-new'
    setTabs(prev => {
      if (prev.find(t => t.id === tabId)) return prev
      return [...prev, { id: tabId, label: 'Neue SOP', type: 'editor', docId: null, closeable: true }]
    })
    setActiveTabId(tabId)
  }, [])

  const openSOPEditorTab = useCallback((sopId, sopCode) => {
    const tabId = `editor-${sopId}`
    setTabs(prev => {
      if (prev.find(t => t.id === tabId)) return prev
      return [...prev, { id: tabId, label: sopCode || `SOP-${sopId}`, type: 'editor', docId: String(sopId), closeable: true }]
    })
    setActiveTabId(tabId)
  }, [])

  const closeTab = useCallback((tabId, e) => {
    e.stopPropagation()
    setTabs(prev => prev.filter(t => t.id !== tabId))
    setActiveTabId(prev => (prev === tabId ? 'sops-list' : prev))
  }, [])

  // ── Data ─────────────────────────────────────────────────────────────────
  const [viewMode, setViewMode] = useState('knowledge')
  const [searchQuery, setSearchQuery] = useState('')
  const [kiSummaryOpen, setKiSummaryOpen] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [activeFilterTab, setActiveFilterTab] = useState('Alle')
  const [sortOrder, setSortOrder] = useState('asc') // 'asc' | 'recent' | 'oldest'
  const [isKIAnalyzing, setIsKIAnalyzing] = useState(false)
  const [kiError, setKIError] = useState('')
  const [kiSummaryText, setKISummaryText] = useState('')
  const [kiSources, setKISources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sops, setSops] = useState([])

  const loadSOPs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const raw = await getSOPs()
      // Raw data — no hardcoded sort; user-controlled dropdown owns ordering
      const mapped = Array.isArray(raw) ? raw.map(mapSOP) : []
      setSops(mapped)
    } catch (err) {
      console.error('Failed to load SOPs:', err)
      setError('SOPs konnten nicht geladen werden.')
      setSops([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSOPs()
  }, [loadSOPs])

  // ── Filtering ─────────────────────────────────────────────────────────────
  const STATUS_MAP = {
    'Freigegeben': ['effective', 'released'],
    'In Prüfung': ['under_review', 'in_review'],
    'Entwurf': ['draft'],
  }

  const filteredSops = sops.filter(sop => {
    const matchesSearch =
      sop.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sop.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (sop.department || '').toLowerCase().includes(searchTerm.toLowerCase())
    if (activeFilterTab === 'Alle') return matchesSearch
    const allowed = STATUS_MAP[activeFilterTab] || []
    return matchesSearch && allowed.includes((sop.status || '').toLowerCase())
  })

  // ── Client-side sorting (works on real backend data) ─────────────────────
  const sortedSops = [...filteredSops].sort((a, b) => {
    if (sortOrder === 'recent') {
      return new Date(b.updated_at_raw || 0) - new Date(a.updated_at_raw || 0)
    }
    if (sortOrder === 'oldest') {
      return new Date(a.updated_at_raw || 0) - new Date(b.updated_at_raw || 0)
    }
    // Default: ascending A→Z by SOP number
    return (a.sop_number || a.code || '').localeCompare(b.sop_number || b.code || '', 'de')
  })

  // ── Actions ──────────────────────────────────────────────────────────────
  const handleOpen = useCallback((sopOrId) => {
    const sop = typeof sopOrId === 'object' ? sopOrId : sops.find(s => s.id === String(sopOrId))
    const id = typeof sopOrId === 'object' ? sopOrId.id : String(sopOrId)
    const code = sop?.sop_number || sop?.code || `SOP-${id}`
    openSOPEditorTab(id, code)
  }, [sops, openSOPEditorTab])

  const handleOpenNewTab = useCallback((sopOrId) => {
    const id = typeof sopOrId === 'object' ? sopOrId.id : String(sopOrId)
    window.open(`/editor/${id}`, '_blank')
  }, [])

  const handleCreate = useCallback(() => {
    openNewSOPTab()
  }, [openNewSOPTab])

  const handleAnalyze = () => {
    const text = searchQuery.trim()
    if (!text) return
    setIsKIAnalyzing(true)
    setKIError('')
    queryAI(text, { category: 'sop' })
      .then((res) => {
        setKISummaryText(res?.answer || 'Keine Antwort vom Backend erhalten.')
        setKISources(Array.isArray(res?.sources) ? res.sources : [])
      })
      .catch((err) => {
        setKIError(err?.message || 'KI-Analyse fehlgeschlagen.')
        setKISummaryText('')
        setKISources([])
      })
      .finally(() => setIsKIAnalyzing(false))
  }

  const handleQuickFilter = (query) => setSearchQuery(query)

  const hasEditorTabs = tabs.some(t => t.type === 'editor')

  return (
    <div className="sops-tabbed-page">

      {/* ── Document tab bar ──────────────────────────────────────────── */}
      {hasEditorTabs && (
        <div className="doc-tab-bar" role="tablist" aria-label="SOP Tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={tab.id === activeTabId}
              className={`doc-tab${tab.id === activeTabId ? ' doc-tab-active' : ''}`}
              onClick={() => setActiveTabId(tab.id)}
            >
              {tab.type === 'editor'
                ? <FileEdit size={13} className="doc-tab-icon" />
                : <List size={13} className="doc-tab-icon" />
              }
              <span className="doc-tab-label">{tab.label}</span>
              {tab.closeable && (
                <span
                  className="doc-tab-close"
                  role="button"
                  aria-label={`${tab.label} schließen`}
                  onClick={(e) => closeTab(tab.id, e)}
                >
                  <X size={11} />
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* ── LIST TAB CONTENT ──────────────────────────────────────────── */}
      <div
        role="tabpanel"
        style={{ display: activeTabId === 'sops-list' ? undefined : 'none' }}
      >
        {/* TABLE VIEW */}
        {viewMode === 'table' && (
          <div className="sops-page">
            <header className="sops-header">
              <div className="header-titles">
                <button
                  className="sops-back-btn"
                  onClick={() => setViewMode('knowledge')}
                >
                  <ArrowLeft size={15} /> SOPs
                </button>
                <h2 className="page-title">Standard Operating Procedures</h2>
              </div>
              <div className="header-actions">
                <button className="export-btn">
                  <Download size={18} /> <span>Exportieren</span>
                </button>
                <button className="new-sop-btn" onClick={handleCreate}>
                  <Plus size={18} /> <span>Neue SOP erstellen</span>
                </button>
              </div>
            </header>

            <section className="sops-controls-card">
              <div className="search-box">
                <Search size={18} className="search-icon" />
                <input
                  type="text"
                  placeholder="Suchen nach Titel, Code oder Verantwortlichen..."
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="filter-group">
                <button className="filter-btn-outline"><Filter size={16} /> <span>Filter</span></button>
                <div className="view-selector">
                  {['Alle', 'Freigegeben', 'In Prüfung', 'Entwurf'].map(tab => (
                    <button
                      key={tab}
                      className={`view-tab ${activeFilterTab === tab ? 'active' : ''}`}
                      onClick={() => setActiveFilterTab(tab)}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
                <select
                  className="sop-sort-select"
                  value={sortOrder}
                  onChange={e => setSortOrder(e.target.value)}
                  aria-label="Sortierung"
                >
                  <option value="asc">A → Z</option>
                  <option value="recent">Neueste zuerst</option>
                  <option value="oldest">Älteste zuerst</option>
                </select>
              </div>
            </section>
            <div className="table-container-card">
              {loading ? (
                <div className="table-loading">
                  <Loader size={20} className="spin" /> Lade SOPs...
                </div>
              ) : error ? (
                <div className="table-loading" style={{ color: 'var(--error)' }}>{error}</div>
              ) : sortedSops.length === 0 ? (
                <div className="table-loading">Keine SOPs gefunden.</div>
              ) : (
                <SOPTable data={sortedSops} onRowClick={(id) => handleOpen(id)} onOpenNewTab={handleOpenNewTab} />
              )}
            </div>
          </div>
        )}

        {/* KNOWLEDGE VIEW */}
        {viewMode === 'knowledge' && (
          <div className="sops-kb-page">
            {/* Breadcrumb tag */}
            <div className="sops-kb-breadcrumb">
              <span className="sops-bc-tag">
                <Plus size={12} /> SOPs
              </span>
            </div>

            {/* Hero card */}
            <div className="sops-hero-card">
              <h1 className="sops-hero-title">Was möchten Sie über Ihre SOPs wissen?</h1>
              <p className="sops-hero-desc">
                Stellen Sie eine Frage im natürlichen Sprachstil. Die KI analysiert Ihre SOPs, verknüpften
                Abweichungen, CAPAs und Audits und liefert eine strukturierte, handlungsbasierte Antwort.
              </p>

              {/* Query input */}
              <div className="sops-query-wrap">
                <textarea
                  className="sops-query-input"
                  placeholder="z.B. Zeige SOPs mit erhöhten Produktionsrisiken? Welche SOP ist am häufigsten angepasst worden?"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  rows={3}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleAnalyze()
                    }
                  }}
                />
                <button
                  className="sops-analyze-btn"
                  onClick={handleAnalyze}
                  disabled={!searchQuery.trim()}
                >
                  <Sparkles size={15} />
                  KI analysieren
                </button>
              </div>

              {/* Action buttons */}
              <div className="sops-action-row">
                <button
                  className="sops-action-btn"
                  onClick={() => sops.length > 0 && handleOpen(sops[0])}
                  disabled={sops.length === 0}
                >
                  <Edit3 size={14} /> SOP bearbeiten
                </button>
                <button
                  className="sops-action-btn"
                  onClick={() => sops.length > 0 && handleOpenNewTab(sops[0])}
                  disabled={sops.length === 0}
                  title="In neuem Tab öffnen"
                >
                  <ExternalLink size={14} /> In neuem Tab
                </button>
                <button className="sops-action-btn" onClick={() => setViewMode('table')}>
                  <FileText size={14} /> Alle SOPs anzeigen
                </button>
                <button className="sops-action-btn sops-action-primary" onClick={handleCreate}>
                  <Plus size={14} /> Neue SOP
                </button>
              </div>

              {/* Quick filter chips */}
              <div className="sops-quick-chips">
                {quickFilters.map(f => (
                  <button key={f} className="sops-quick-chip" onClick={() => handleQuickFilter(f)}>
                    {f}
                  </button>
                ))}
              </div>
            </div>

            {/* KI Summary */}
            <KISummary
              open={kiSummaryOpen}
              onToggle={() => setKiSummaryOpen(v => !v)}
              query={searchQuery}
              summaryText={kiSummaryText}
              sources={kiSources}
              loading={isKIAnalyzing}
              error={kiError}
            />
            {/* Relevant SOPs from backend */}
            <div className="sops-section-title-row">
              <h2 className="sops-section-title">Relevante SOPs im aktuellen Kontext</h2>
              <select
                className="sop-sort-select"
                value={sortOrder}
                onChange={e => setSortOrder(e.target.value)}
                aria-label="Sortierung"
              >
                <option value="asc">A → Z</option>
                <option value="recent">Neueste zuerst</option>
                <option value="oldest">Älteste zuerst</option>
              </select>
            </div>

            <div className="sops-cards-grid">
              {loading && (
                <div style={{ padding: '24px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Loader size={16} /> Lade SOPs...
                </div>
              )}
              {!loading && error && (
                <div style={{ padding: '24px', color: 'var(--error)' }}>{error}</div>
              )}
              {!loading && !error && sops.length === 0 && (
                <div style={{ padding: '24px', color: 'var(--text-muted)' }}>
                  Keine SOPs in der Datenbank gefunden.
                </div>
              )}
              {!loading && sortedSops.map(sop => (
                <SOPCard
                  key={sop.id}
                  sop={sop}
                  onOpen={handleOpen}
                  onOpenNewTab={handleOpenNewTab}
                  onEdit={handleOpen}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── EDITOR TABS CONTENT ──────────────────────────────────────────── */}
      {tabs.filter(t => t.type === 'editor').map(tab => (
        <div
          key={tab.id}
          role="tabpanel"
          className="editor-tab-wrapper"
          style={{ display: tab.id === activeTabId ? undefined : 'none' }}
        >
          <EditorPage
            isEmbedded
            initialDocId={tab.docId !== undefined ? tab.docId : null}
          />
        </div>
      ))}
    </div>
  )
}
