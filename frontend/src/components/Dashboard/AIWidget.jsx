import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useLocation } from 'react-router-dom'
import { Send, Zap } from 'lucide-react'
import { queryAI } from '../../api/editorApi'
import './DashboardComponents.css'

// Context-aware quick suggestions based on current route
const SUGGESTIONS_BY_ROUTE = {
  '/sops': [
    'Welche SOP ist besonders relevant?',
    'Gab es Audit-Bezug?',
    'Was war die letzte Abweichung?',
    'Zusammenfassung letzter Woche',
  ],
  default: [
    'Welche SOP ist besonders relevant?',
    'Gab es Audit-Bezug?',
    'Was war die letzte Abweichung?',
    'Zusammenfassung letzter Woche',
  ],
}

// Initial greeting from AI (loaded on first render)
const GREETING_MESSAGE = {
  id: 'greeting',
  role: 'ai',
  text: 'Guten Morgen, Martina. Heute haben Sie 3 dringende Aufgaben und 3 neue Abweichungen. Soll ich mit den kritischsten beginnen?',
  tags: ['DEV-2025-031', 'CAPA-2025-03'],
}

export default function AIWidget() {
  const location = useLocation()
  const [messages, setMessages] = useState([GREETING_MESSAGE])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const chatEndRef = useRef(null)

  const suggestions =
    SUGGESTIONS_BY_ROUTE[location.pathname] ?? SUGGESTIONS_BY_ROUTE.default

  // Auto-scroll to bottom whenever messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || sending) return

    // Append user message immediately
    const userMsg = { id: Date.now(), role: 'user', text: trimmed }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setSending(true)

    try {
      // TODO: POST /api/ai/query — connect when backend AI endpoint is ready
      const result = await queryAI(trimmed)
      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        text: result.answer || result.text || result.response || '—',
        tags: result.sources?.map(s => s.label) ?? [],
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err) {
      // Graceful error message in chat
      const errMsg = {
        id: Date.now() + 1,
        role: 'ai',
        text: err.status === 404 || err.message?.includes('not yet implemented')
          ? 'Das KI-Backend ist noch nicht verbunden. (TODO: /api/ai/query)'
          : `Fehler: ${err.message}`,
        isError: true,
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setSending(false)
    }
  }, [sending])

  const handleSend = () => sendMessage(input)

  // Clicking a suggestion triggers the actual query immediately
  const handleSuggestionClick = (text) => sendMessage(text)

  const contextLabel = location.pathname === '/sops'
    ? 'Kontext: SOP-Ansicht'
    : 'Kontext: Keine Analyse, Startscreen'

  return (
    <div className="ai-widget-container">
      {/* Header (n_93fb9) */}
      <div className="ai-widget-header-section">
        {/* Title row with status dot, title, and Aktiv badge (n_00925, n_93f3c, n_36ff5, n_a93c8, n_cf5e4) */}
        <div className="ai-widget-header-row">
          <div className="ai-widget-title-group">
            <span className="ai-status-dot" />
            <h3 className="ai-widget-title">KI Assistent</h3>
          </div>
          <span className="ai-aktiv-badge">Aktiv</span>
        </div>
        <div className="ai-widget-divider" />
      </div>

      {/* Context section (n_e1120) */}
      <div className="ai-context-section">
        {/* Context label row (n_36782, n_8a4b0, n_1632b) */}
        <div className="ai-context-row">
          <Zap size={14} className="ai-context-icon" />
          <span className="ai-context-label">{contextLabel}</span>
        </div>

        {/* Input and send button (n_af201, n_dfc55, n_61f05) */}
        <div className="ai-context-input-group">
          <input
            type="text"
            className="ai-context-input"
            placeholder="Frage zur SOP stellen…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            disabled={sending}
          />
          <button
            className="ai-context-send-btn"
            onClick={handleSend}
            disabled={sending || !input.trim()}
            aria-label="Senden"
          >
            Senden
          </button>
        </div>
      </div>

      <div className="ai-widget-divider" />

      {/* Chat message bubble (n_50e03) */}
      <div className="ai-messages-section">
        {messages.length > 0 && (
          <div className="ai-greeting-bubble">
            <p className="ai-greeting-text">{messages[0]?.text}</p>
            {messages[0]?.tags && messages[0]?.tags.length > 0 && (
              <div className="ai-message-tags">
                {messages[0]?.tags.map(tag => (
                  <span key={tag} className="ai-message-tag">{tag}</span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Additional messages */}
        {messages.slice(1).map(m => (
          <div
            key={m.id}
            className={`ai-chat-message ${m.role}${m.isError ? ' error' : ''}`}
          >
            <p>{m.text}</p>
            {m.tags && m.tags.length > 0 && (
              <div className="ai-message-tags">
                {m.tags.map(tag => (
                  <span key={tag} className="ai-message-tag">{tag}</span>
                ))}
              </div>
            )}
          </div>
        ))}

        {sending && (
          <div className="ai-typing-indicator">
            <span /><span /><span />
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="ai-widget-divider" />

      {/* Quick suggestions section (n_8bfec, n_497dc, n_a2601, n_11cef, n_9d5ed) */}
      <div className="ai-quick-section">
        <h4 className="ai-quick-title">Schnelle Fragen</h4>
        <div className="ai-quick-list">
          {suggestions.map(text => (
            <button
              key={text}
              className="ai-quick-item"
              onClick={() => handleSuggestionClick(text)}
              disabled={sending}
            >
              {text}
            </button>
          ))}
        </div>
      </div>

      <div className="ai-widget-divider" />

      {/* Bottom input area (n_5a7d9, n_0cb35, n_afcae) */}
      <div className="ai-bottom-input-section">
        <div className="ai-bottom-input-group">
          <input
            type="text"
            placeholder="Frage zur SOP stellen…"
            className="ai-bottom-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            disabled={sending}
          />
          <button
            className="ai-bottom-send-btn"
            onClick={handleSend}
            disabled={sending || !input.trim()}
            aria-label="Senden"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}
