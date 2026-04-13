import React, { useState } from 'react'
import {
  Search, Filter, Mail, Bell, Sparkles, LayoutDashboard,
  ClipboardList, AlertTriangle, Scale, FileSearch, GitBranch,
  Settings, HelpCircle, LogOut, CheckCircle, File, ExternalLink,
  FileText, MessageCircle
} from 'lucide-react'
import './StartTab.css'

const statsData = [
  { id: 'sops',   label: 'Aktive SOPs',           value: '142', sub: '+3 diese Woche',    trend: 'up' },
  { id: 'devs',   label: 'Offene Abweichungen',    value: '7',   sub: '+3 neu heute',       trend: 'warn' },
  { id: 'capa',   label: 'CAPA Maßnahmen',         value: '3',   sub: '1 fällig heute',     trend: 'warn' },
  { id: 'audit',  label: 'Audit Findings',         value: '94%', sub: 'Alle in Bearbeitung',trend: 'ok' },
  { id: 'review', label: 'SOPs in Überprüfung',    value: '11',  sub: '2 warten auf Sie',   trend: 'up' },
]

const activities = [
  { id: 1, type: 'warn',   title: 'Neue Abweichung erfasst – Reinigungsprotokoll fehlt',      meta: 'Vor 23 Minuten · Linie 3 · von J. Berger',       ref: 'DEV-2025-031', status: 'Neu',     statusColor: 'error'   },
  { id: 2, type: 'file',   title: 'SOP-QA-042 Version 5 zur Prüfung freigegeben',              meta: 'Vor 1 Stunde · von Ihnen bearbeitet',             ref: 'SOP-QA-042',   status: 'Prüfung', statusColor: 'primary' },
  { id: 3, type: 'check',  title: 'CAPA-Wirksamkeitsprüfung abgeschlossen',                    meta: 'Vor 2 Stunden · von M. Fischer',                  ref: 'CAPA-2024-07', status: 'Erledigt',statusColor: 'success' },
  { id: 4, type: 'search', title: 'Audit Finding beantwortet – FDA Inspektion 2024',           meta: 'Gestern, 15:42 · von T. Schwarz',                 ref: 'AUD-2024-02',  status: 'Erledigt',statusColor: 'success' },
  { id: 5, type: 'open',   title: 'Abweichung eskaliert – Temperaturüberschreitung Lager',     meta: 'Gestern, 15:42 · von T. Schwarz',                 ref: 'DEV-2025-029', status: 'Offen',   statusColor: 'warning' },
  { id: 6, type: 'draft',  title: 'SOP-QA-031 – Neue Revision gestartet',                     meta: 'Vor 2 Tagen · von Ihnen',                         ref: 'SOP-QA-031',   status: 'Entwurf', statusColor: 'muted'   },
]

const tasks = [
  { id: 1, title: 'SOP-QA-042 Abschnitt 4.3 überprüfen',           category: 'Reinigungsverfahren', ref: 'SOP-QA-042',   due: 'Heute',    done: false },
  { id: 2, title: 'CAPA-2025-03 Wirksamkeit prüfen und bestätigen', category: 'Sterilisation',       ref: 'CAPA-2025-03', due: 'Heute',    done: false },
  { id: 3, title: 'Abweichung DEV-2025-029 bewerten',               category: 'Lager Temp',          ref: 'DEV-2025-029', due: 'Morgen',   done: false },
  { id: 4, title: 'SOP-QA-031 Version 3 freigeben',                 category: 'Validierung',         ref: 'SOP-QA-031',   due: 'Erledigt', done: true  },
  { id: 5, title: 'Audit-Antwort AUD-2024-02 einreichen',           category: 'FDA Inspektion',      ref: 'AUD-2024-02',  due: 'Erledigt', done: true  },
]

const chatMessages = [
  {
    id: 1, role: 'ai',
    text: 'Guten Morgen, Martina. Heute haben Sie 3 dringende Aufgaben und 3 neue Abweichungen. Soll ich mit den kritischsten beginnen?',
    tags: ['DEV-2025-031', 'CAPA-2025-03'],
  },
  {
    id: 2, role: 'user',
    text: 'Was ist bei DEV-2025-031 passiert?',
  },
  {
    id: 3, role: 'ai',
    text: 'DEV-2025-031 wurde heute um 07:14 Uhr erfasst. Ursache: fehlendes Reinigungsprotokoll nach Chargenwechsel auf Linie 3. Verknüpft mit SOP-QA-042.',
    tags: ['SOP-QA-042', 'Linie 3'],
  },
  {
    id: 4, role: 'ai',
    text: 'Soll ich die SOP direkt öffnen oder die Abweichung zuerst bewerten?',
  },
]

const suggestions = [
  'Welche Aufgaben sind heute dringend?',
  'Zeige alle offenen Abweichungen',
  'Welche SOPs warten auf Prüfung?',
  'Zusammenfassung meiner Woche',
]

const activityIconMap = {
  warn:   { icon: AlertTriangle, cls: 'aic-warn'    },
  file:   { icon: File,          cls: 'aic-primary'  },
  check:  { icon: CheckCircle,   cls: 'aic-success'  },
  search: { icon: Search,        cls: 'aic-muted'    },
  open:   { icon: ExternalLink,  cls: 'aic-error'    },
  draft:  { icon: FileText,      cls: 'aic-muted'    },
}

function ActivityIcon({ type }) {
  const { icon: Icon, cls } = activityIconMap[type] || { icon: File, cls: 'aic-muted' }
  return <span className={`st-aic ${cls}`}><Icon size={13} /></span>
}

export default function StartTab() {
  const [activeFilter, setActiveFilter] = useState('Alle')
  const [chatInput, setChatInput] = useState('')

  return (
    <div className="start-tab">

      {/* ── SIDEBAR ── */}
      <aside className="st-sidebar">
        <div className="st-sidebar-inner">

          <div className="st-brand">
            <span className="st-brand-icon"><Sparkles size={16} /></span>
            <span className="st-brand-name">Cybrain QS</span>
          </div>

          <div className="st-topbar">
            <div className="st-search">
              <Search size={13} />
              <span>Suchen</span>
            </div>
            <button className="st-icon-btn"><Filter size={13} /></button>
          </div>

          <div className="st-user-row">
            <button className="st-icon-btn"><Mail size={15} /></button>
            <button className="st-icon-btn"><Bell size={15} /></button>
            <div className="st-avatar-circle">H</div>
            <div className="st-user-info">
              <span className="st-user-name">Haider K.</span>
              <span className="st-user-email">haiderkhane@gmail.com</span>
            </div>
          </div>

          <p className="st-nav-section">Hauptmenü</p>
          <nav className="st-nav">
            <a href="#" className="st-nav-item"><Search size={15} /><span>Wissenssuche</span></a>
            <a href="#" className="st-nav-item"><MessageCircle size={15} /><span>Gespräche</span></a>
            <a href="#" className="st-nav-item st-nav-active">
              <LayoutDashboard size={15} /><span>Start</span>
              <span className="st-badge">12</span>
            </a>
            <a href="#" className="st-nav-item">
              <ClipboardList size={15} /><span>SOPs</span>
              <span className="st-badge">12</span>
            </a>
          </nav>

          <p className="st-nav-section">Qualität</p>
          <nav className="st-nav">
            <a href="#" className="st-nav-item">
              <AlertTriangle size={15} /><span>Abweichungen</span>
              <span className="st-badge st-badge-error">3</span>
            </a>
            <a href="#" className="st-nav-item"><Scale size={15} /><span>CAPA Maßnahmen</span></a>
            <a href="#" className="st-nav-item"><FileSearch size={15} /><span>Audit Findings</span></a>
            <a href="#" className="st-nav-item"><GitBranch size={15} /><span>Entscheidungen</span></a>
          </nav>
        </div>

        <nav className="st-nav st-nav-bottom">
          <a href="#" className="st-nav-item"><Settings size={15} /><span>Einstellungen</span></a>
          <a href="#" className="st-nav-item"><HelpCircle size={15} /><span>Helfen</span></a>
          <a href="#" className="st-nav-item st-nav-logout"><LogOut size={15} /><span>Abmelden</span></a>
        </nav>
      </aside>

      {/* ── MAIN ── */}
      <main className="st-main">

        {/* Date bar */}
        <div className="st-datebar">
          <div className="st-date">
            <span className="st-date-day">07</span>
            <span className="st-date-label">April 2026 – Dienstag</span>
          </div>
          <button className="st-ki-btn">
            <Sparkles size={13} />
            KI befragen
          </button>
        </div>

        {/* Welcome banner */}
        <div className="st-welcome">
          <div className="st-welcome-text">
            <p className="st-welcome-back">Willkommen zurück</p>
            <h2 className="st-welcome-name">Guten Morgen, Haider!</h2>
            <p className="st-welcome-focus">
              Ihr heutiger Fokus: 3 offene Aufgaben – 2 SOPs zur Überprüfung
            </p>
          </div>
          <div className="st-status-badges">
            <span className="st-status-badge st-sbadge-error">
              <span className="st-dot" />&nbsp;3 neue Abweichungen
            </span>
            <span className="st-status-badge st-sbadge-warning">
              <span className="st-dot" />&nbsp;1 CAPA fällig
            </span>
            <span className="st-status-badge st-sbadge-success">
              <span className="st-dot" />&nbsp;System aktiv
            </span>
          </div>
        </div>

        {/* Stats row */}
        <div className="st-stats">
          {statsData.map(s => (
            <div key={s.id} className="st-stat-card">
              <p className="st-stat-label">{s.label}</p>
              <p className="st-stat-value">{s.value}</p>
              <p className={`st-stat-sub st-sub-${s.trend}`}>{s.sub}</p>
            </div>
          ))}
        </div>

        {/* Content grid */}
        <div className="st-grid">

          {/* Letzte Aktivitäten */}
          <div className="st-card">
            <div className="st-card-header">
              <h3>Letzte Aktivitäten</h3>
              <a href="#" className="st-link">Alle anzeigen →</a>
            </div>
            <div className="st-filter-tabs">
              {['Alle', 'SOPs', 'Abweichungen', 'CAPAs'].map(f => (
                <button
                  key={f}
                  className={`st-tab ${activeFilter === f ? 'st-tab-active' : ''}`}
                  onClick={() => setActiveFilter(f)}
                >
                  {f}
                </button>
              ))}
            </div>
            <div className="st-list">
              {activities.map(a => (
                <div key={a.id} className="st-activity-item">
                  <ActivityIcon type={a.type} />
                  <div className="st-item-body">
                    <p className="st-item-title">{a.title}</p>
                    <p className="st-item-meta">{a.meta}</p>
                    <div className="st-tags">
                      <span className="st-tag st-tag-ref">{a.ref}</span>
                      <span className={`st-tag st-tag-status st-s-${a.statusColor}`}>{a.status}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Meine Aufgaben */}
          <div className="st-card">
            <div className="st-card-header">
              <h3>Meine Aufgaben</h3>
              <a href="#" className="st-link">Alle anzeigen →</a>
            </div>
            <div className="st-list">
              {tasks.map(t => (
                <div key={t.id} className={`st-task-item ${t.done ? 'st-task-done' : ''}`}>
                  <span className="st-task-check">
                    {t.done
                      ? <CheckCircle size={15} className="st-check-filled" />
                      : <span className="st-check-empty" />}
                  </span>
                  <div className="st-item-body">
                    <p className="st-item-title">{t.title}</p>
                    <p className="st-item-meta">{t.category}</p>
                    <div className="st-tags">
                      <span className="st-tag st-tag-ref">{t.ref}</span>
                      <span className={`st-tag st-tag-status ${
                        t.due === 'Erledigt' ? 'st-s-success'
                        : t.due === 'Morgen'  ? 'st-s-muted'
                        : 'st-s-warning'
                      }`}>{t.due}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </main>

      {/* ── AI PANEL ── */}
      <aside className="st-ai-panel">

        <div className="st-ai-header">
          <div className="st-context-row">
            <span className="st-context-label">Kontext:</span>
            <span className="st-context-chip">Startseite</span>
            <span className="st-context-chip">M. Kaufmann</span>
          </div>
          <div className="st-ai-titlerow">
            <div className="st-ai-title">
              <Sparkles size={14} />
              <span>KI befragen</span>
            </div>
            <span className="st-aktiv">Aktiv</span>
          </div>
        </div>

        <div className="st-chat-messages">
          {chatMessages.map(m => (
            <div key={m.id} className={`st-chat-msg ${m.role === 'user' ? 'st-msg-user' : 'st-msg-ai'}`}>
              {m.role === 'ai'
                ? <span className="st-ai-avatar"><Sparkles size={11} /></span>
                : <span className="st-user-avatar-sm">KH</span>
              }
              <div className="st-msg-bubble">
                <p>{m.text}</p>
                {m.tags && (
                  <div className="st-tags" style={{ marginTop: 6 }}>
                    {m.tags.map(tag => (
                      <span key={tag} className="st-tag st-tag-ref">{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="st-ai-input-area">
          <p className="st-suggestions-label">Vorgeschlagene Aktionen</p>
          <div className="st-suggestion-chips">
            {suggestions.map(s => (
              <button key={s} className="st-suggestion-chip" onClick={() => setChatInput(s)}>
                {s}
              </button>
            ))}
          </div>

          <div className="st-input-row">
            <input
              className="st-chat-input"
              placeholder="Frage zur SOP stellen..."
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
            />
          </div>

          <div className="st-action-row">
            <button className="st-action-btn st-btn-primary">Senden</button>
            <button className="st-action-btn st-btn-ghost">Kopieren</button>
            <button className="st-action-btn st-btn-ghost">In Editor</button>
          </div>
        </div>

      </aside>
    </div>
  )
}
