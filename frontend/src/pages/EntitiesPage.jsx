import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Plus, Download, Loader, AlertTriangle, ShieldCheck, ClipboardCheck, HelpCircle, RefreshCw, ExternalLink } from 'lucide-react'
import { getDeviations, getCAPAs, getAuditFindings, getDecisions, getDeviationContext } from '../api/editorApi'
import './EntitiesPage.css'

const typeConfig = {
  deviations: {
    title: 'Abweichungen (Deviations)',
    fetch: getDeviations,
    icon: <AlertTriangle className="text-amber-500" />,
    color: 'amber',
    codeKey: 'deviation_number'
  },
  capas: {
    title: 'CAPA Maßnahmen',
    fetch: getCAPAs,
    icon: <ShieldCheck className="text-emerald-500" />,
    color: 'emerald',
    codeKey: 'capa_number'
  },
  audits: {
    title: 'Audit Findings',
    fetch: getAuditFindings,
    icon: <ClipboardCheck className="text-blue-500" />,
    color: 'blue',
    codeKey: 'finding_number'
  },
  decisions: {
    title: 'Entscheidungen (Decisions)',
    fetch: getDecisions,
    icon: <HelpCircle className="text-purple-500" />,
    color: 'purple',
    codeKey: 'decision_number'
  }
}

export default function EntitiesPage({ type }) {
  const navigate = useNavigate()
  const config = typeConfig[type]
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortOrder, setSortOrder] = useState('latest')
  const [showAllItems, setShowAllItems] = useState(false)
  const [selectedContext, setSelectedContext] = useState(null)
  const [contextLoadingId, setContextLoadingId] = useState(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await config.fetch()
      setItems(data || [])
    } catch (err) {
      setError(`Fehler beim Laden von ${config.title}`)
    } finally {
      setLoading(false)
    }
  }, [config])

  useEffect(() => {
    loadData()
  }, [loadData])

  const filteredItems = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()
    const byTerm = items.filter((item) =>
      `${item.title || ''} ${item.description_text || ''} ${item[config.codeKey] || ''} ${item.category || ''} ${item.site || ''}`
        .toLowerCase()
        .includes(term),
    )

    const byStatus = byTerm.filter((item) => {
      if (statusFilter === 'all') return true
      return (item.external_status || item.acceptance_status || '').toLowerCase() === statusFilter
    })

    return [...byStatus].sort((a, b) => {
      if (sortOrder === 'oldest') return new Date(a.created_at || 0) - new Date(b.created_at || 0)
      if (sortOrder === 'title') return `${a.title || ''}`.localeCompare(`${b.title || ''}`, 'de')
      return new Date(b.created_at || 0) - new Date(a.created_at || 0)
    })
  }, [items, config.codeKey, searchTerm, statusFilter, sortOrder])

  const isDeviations = type === 'deviations'

  const criticalItems = useMemo(
    () => filteredItems.filter((item) => (item.impact_level || '').toLowerCase() === 'high' || (item.external_status || '').toLowerCase() === 'critical'),
    [filteredItems],
  )

  const causesData = useMemo(() => {
    if (!isDeviations) return []
    const buckets = [
      { key: 'process', label: 'Prozessabweichung', colorClass: 'entities-cause-red' },
      { key: 'equipment', label: 'Geräteausfall', colorClass: 'entities-cause-orange' },
      { key: 'training', label: 'Schulungsdefizit', colorClass: 'entities-cause-blue' },
      { key: 'documentation', label: 'Dokumentationsfehler', colorClass: 'entities-cause-purple' },
    ]
    const normalize = (item) => `${item.category || ''} ${item.root_cause_text || ''} ${item.title || ''}`.toLowerCase()
    const totals = buckets.map((bucket) => {
      let count = 0
      filteredItems.forEach((item) => {
        const txt = normalize(item)
        if (
          (bucket.key === 'process' && (txt.includes('prozess') || txt.includes('process'))) ||
          (bucket.key === 'equipment' && (txt.includes('gerät') || txt.includes('equipment') || txt.includes('anlage'))) ||
          (bucket.key === 'training' && (txt.includes('training') || txt.includes('schulung'))) ||
          (bucket.key === 'documentation' && (txt.includes('dokument') || txt.includes('documentation')))
        ) {
          count += 1
        }
      })
      return { ...bucket, count }
    })
    const max = Math.max(...totals.map((x) => x.count), 1)
    return totals.map((item) => ({ ...item, width: `${Math.max((item.count / max) * 100, item.count > 0 ? 12 : 0)}%` }))
  }, [filteredItems, isDeviations])

  const monthlyData = useMemo(() => {
    if (!isDeviations) return []
    const now = new Date()
    const months = Array.from({ length: 6 }).map((_, idx) => {
      const d = new Date(now.getFullYear(), now.getMonth() - (5 - idx), 1)
      const key = `${d.getFullYear()}-${d.getMonth()}`
      const label = d.toLocaleString('en-US', { month: 'short' })
      return { key, label, month: d.getMonth(), year: d.getFullYear() }
    })

    return months.map((entry) => {
      const count = filteredItems.reduce((acc, item) => {
        const dt = item.created_at ? new Date(item.created_at) : null
        if (!dt || Number.isNaN(dt.getTime())) return acc
        return dt.getMonth() === entry.month && dt.getFullYear() === entry.year ? acc + 1 : acc
      }, 0)
      return { month: entry.label, count }
    })
  }, [filteredItems, isDeviations])

  const topItems = useMemo(() => (showAllItems ? filteredItems : filteredItems.slice(0, 6)), [filteredItems, showAllItems])

  const uniqueStatuses = useMemo(() => {
    const base = new Set()
    items.forEach((item) => {
      const st = (item.external_status || item.acceptance_status || '').toLowerCase()
      if (st) base.add(st)
    })
    return ['all', ...Array.from(base)]
  }, [items])

  const handleAnalyzeClick = () => {
    setShowAllItems(true)
  }

  const openContext = async (item) => {
    if (!isDeviations) return
    setContextLoadingId(item.id)
    try {
      const ctx = await getDeviationContext(item.id)
      setSelectedContext({
        id: item.id,
        title: item.title || item.description_text || item.deviation_number || 'Abweichung',
        data: ctx,
      })
    } catch (ctxErr) {
      setSelectedContext({
        id: item.id,
        title: item.title || item.deviation_number || 'Abweichung',
        error: 'Kontext konnte nicht geladen werden.',
      })
    } finally {
      setContextLoadingId(null)
    }
  }

  const openLinkedSOP = (item) => {
    const linked = selectedContext?.data?.related_sops || []
    if (linked.length > 0) {
      navigate(`/editor/${linked[0].id}`)
      return
    }
    if (item?.sop_id) navigate(`/editor/${item.sop_id}`)
  }

  return (
    <div className={`entities-page ${isDeviations ? 'entities-page-deviations' : ''}`}>
      <header className="entities-hero">
        <div className="entities-pill">
          <span>Abweichungen</span>
        </div>
        <h1 className="entities-title">Was möchten Sie über Ihre Abweichungen wissen?</h1>
        <p className="entities-subtitle">
          Stellen Sie eine Frage — die KI analysiert alle {config.title}, verknüpfte SOPs, CAPAs und Audits und liefert eine
          Zusammenfassung mit Ursachen, Mustern und Empfehlungen.
        </p>

        <div className="entities-search-row">
          <div className="entities-search-box">
            <Search size={16} />
            <input
              type="text"
              placeholder="z.B. Welche SOPs sind besonders risikoreich? Was waren die Hauptursachen der Abweichungen in Q1?"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="entities-primary-btn" type="button" onClick={handleAnalyzeClick}>
            <Search size={14} /> Kontext analysieren
          </button>
        </div>

        <div className="entities-toolbar-row">
          <button className="entities-outline-btn" type="button"><Plus size={14} /> Neue Abweichung melden</button>
          <button className="entities-outline-btn" type="button"><Download size={14} /> Bericht exportieren</button>
          <button className="entities-outline-btn entities-muted-btn" type="button" onClick={() => setShowAllItems((v) => !v)}>
            {showAllItems ? 'Kompakt anzeigen' : 'Alle anzeigen'}
          </button>
          <button className="entities-outline-btn" type="button" onClick={loadData}>
            <RefreshCw size={14} /> Neu laden
          </button>
          <select className="entities-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            {uniqueStatuses.map((st) => (
              <option key={st} value={st}>{st === 'all' ? 'Alle Status' : st}</option>
            ))}
          </select>
          <select className="entities-select" value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
            <option value="latest">Neueste zuerst</option>
            <option value="oldest">Älteste zuerst</option>
            <option value="title">Titel A-Z</option>
          </select>
        </div>

        <div className="entities-suggestions">
          {[
            'Was waren die Hauptursachen der Abweichungen in Q1?',
            'Welche SOPs haben die meisten Abweichungen?',
            'Gibt es wiederkehrende Muster?',
            'Welche Abweichungen sind noch offen?',
          ].map((s) => (
            <button key={s} className="entities-suggestion-chip" type="button">{s}</button>
          ))}
        </div>
      </header>

      {isDeviations && criticalItems.length > 0 ? (
        <section className="entities-alert-bar">
          <div className="entities-alert-left">
            <AlertTriangle size={16} />
            <div>
              <strong>{criticalItems.length} kritische Abweichungen erfordern sofortige Aufmerksamkeit</strong>
              <p>Priorisieren Sie Untersuchungen und Fristen, um Produktionsrisiken zu reduzieren.</p>
            </div>
          </div>
          <div className="entities-alert-actions">
            <button type="button" className="entities-alert-btn entities-alert-btn-solid">Jetzt analysieren</button>
            <button type="button" className="entities-alert-btn">KI fragen</button>
          </div>
        </section>
      ) : null}

      <div className="entities-grid">
        <section className="entities-card entities-list-card">
          <div className="entities-card-head">
            <h2>Aktuelle & relevante {isDeviations ? 'Abweichungen' : config.title}</h2>
            <button type="button">Alle {filteredItems.length} anzeigen</button>
          </div>
          {loading ? (
            <div className="entities-loading-row"><Loader size={18} className="spin" /> Lade Daten...</div>
          ) : error ? (
            <div className="entities-loading-row entities-error">{error}</div>
          ) : topItems.length === 0 ? (
            <div className="entities-loading-row">Keine Einträge gefunden.</div>
          ) : (
            <div className="entities-items">
              {topItems.map((item) => (
                <article key={item.id} className="entities-item">
                  <div className="entities-item-top">
                    <span className="entities-item-code">{item[config.codeKey] || '—'}</span>
                    <span className="entities-item-status">{item.external_status || item.acceptance_status || 'open'}</span>
                  </div>
                  <h3>{item.title || item.description_text?.slice(0, 80) || 'Unbenannt'}</h3>
                  <p>{item.site ? `${item.site} · ` : ''}{item.created_at ? new Date(item.created_at).toLocaleDateString('de-DE') : '—'}</p>
                  <div className="entities-item-tags">
                    {item.deviation_number ? <span>{item.deviation_number}</span> : null}
                    {item.impact_level ? <span>{item.impact_level}</span> : null}
                    {item.category ? <span>{item.category}</span> : null}
                  </div>
                  <div className="entities-item-actions">
                    <button type="button" className="entities-item-action-primary" onClick={() => setSearchTerm(item.title || item.deviation_number || '')}>Analysieren</button>
                    <button type="button" onClick={() => openContext(item)} disabled={contextLoadingId === item.id}>
                      {contextLoadingId === item.id ? 'Lädt...' : 'Kontext'}
                    </button>
                    <button type="button" onClick={() => openLinkedSOP(item)}>SOP öffnen</button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="entities-card entities-insights-card">
          <div className="entities-mini-card">
            <div className="entities-mini-head">
              <h3>Häufigste Ursachen · Q1 2025</h3>
              <span>{filteredItems.length} Abweichungen</span>
            </div>
            <div className="entities-causes">
              {causesData.map((cause) => (
                <div key={cause.key} className="entities-cause-row">
                  <span>{cause.label}</span>
                  <div className="entities-cause-bar-track">
                    <div className={`entities-cause-bar ${cause.colorClass}`} style={{ width: cause.width }} />
                  </div>
                  <strong>{cause.count}</strong>
                </div>
              ))}
            </div>
          </div>

          <div className="entities-mini-card">
            <div className="entities-mini-head">
              <h3>Abweichungen nach Monat</h3>
              <span>6 Monate</span>
            </div>
            <div className="entities-months">
              {monthlyData.map((m) => (
                <div key={m.month} className="entities-month-row">
                  <span>{m.month}</span>
                  <div className="entities-dots">
                    {Array.from({ length: Math.min(m.count, 8) }).map((_, idx) => (
                      <i key={`${m.month}-${idx}`} />
                    ))}
                  </div>
                  <strong>{m.count}</strong>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      {isDeviations && selectedContext ? (
        <section className="entities-card entities-context-card">
          <div className="entities-card-head">
            <h2>Kontext: {selectedContext.title}</h2>
            <button type="button" onClick={() => setSelectedContext(null)}>Schließen</button>
          </div>
          {selectedContext.error ? (
            <div className="entities-loading-row entities-error">{selectedContext.error}</div>
          ) : (
            <div className="entities-context-grid">
              <article>
                <h4>Verknüpfte SOPs ({selectedContext.data.related_sops?.length || 0})</h4>
                <div className="entities-context-list">
                  {(selectedContext.data.related_sops || []).slice(0, 8).map((sop) => (
                    <button key={sop.id} type="button" className="entities-context-chip" onClick={() => navigate(`/editor/${sop.id}`)}>
                      {sop.sop_number || 'SOP'} · {sop.title || 'Untitled'} <ExternalLink size={12} />
                    </button>
                  ))}
                </div>
              </article>
              <article>
                <h4>Verknüpfte CAPAs ({selectedContext.data.related_capas?.length || 0})</h4>
                <div className="entities-context-list">
                  {(selectedContext.data.related_capas || []).slice(0, 8).map((capa) => (
                    <span key={capa.id} className="entities-context-chip">{capa.capa_number || 'CAPA'} · {capa.title || 'Untitled'}</span>
                  ))}
                </div>
              </article>
              <article>
                <h4>Audit Findings ({selectedContext.data.related_audits?.length || 0})</h4>
                <div className="entities-context-list">
                  {(selectedContext.data.related_audits || []).slice(0, 8).map((audit) => (
                    <span key={audit.id} className="entities-context-chip">{audit.finding_number || audit.audit_number || 'Audit'}</span>
                  ))}
                </div>
              </article>
              <article>
                <h4>Entscheidungen ({selectedContext.data.related_decisions?.length || 0})</h4>
                <div className="entities-context-list">
                  {(selectedContext.data.related_decisions || []).slice(0, 8).map((decision) => (
                    <span key={decision.id} className="entities-context-chip">{decision.decision_number || 'Decision'} · {decision.title || 'Untitled'}</span>
                  ))}
                </div>
              </article>
            </div>
          )}
        </section>
      ) : null}

      {!isDeviations ? (
        <section className="entities-legacy-table">
          <header className="entities-legacy-header">
            <div className="entities-legacy-title">
              {config.icon}
              <h2>{config.title}</h2>
            </div>
            <div className="entities-legacy-actions">
              <button className="entities-outline-btn"><Download size={16} /> Export</button>
              <button className="entities-primary-btn"><Plus size={16} /> Neu hinzufügen</button>
            </div>
          </header>

          <div className="entities-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nummer</th>
                  <th>Titel / Beschreibung</th>
                  <th>Status</th>
                  <th>Erstellt am</th>
                  <th>Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan="5"><div className="entities-loading-row"><Loader className="spin" size={18} /> Lade Daten...</div></td></tr>
                ) : filteredItems.length === 0 ? (
                  <tr><td colSpan="5"><div className="entities-loading-row">Keine Einträge gefunden.</div></td></tr>
                ) : filteredItems.map((item) => (
                  <tr key={item.id}>
                    <td>{item[config.codeKey] || '—'}</td>
                    <td>{item.title || item.description_text?.slice(0, 50) || 'Unbenannt'}</td>
                    <td>{item.external_status || item.acceptance_status || 'Offen'}</td>
                    <td>{new Date(item.created_at).toLocaleDateString('de-DE')}</td>
                    <td>Details</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  )
}
