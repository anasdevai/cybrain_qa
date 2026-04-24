import React, { useState, useRef, useEffect } from 'react'
import { Plus, ArrowUp, Search, MessageCircle } from 'lucide-react'
import ChatMessage from './ChatMessage'
import ChatTypingIndicator from './ChatTypingIndicator'
import SourceTag from './SourceTag'
import './ChatPanel.css'

/**
 * ChatPanel — Main chat detail view with header, messages & input.
 */
export default function ChatPanel({ conversation, onSendMessage, isAwaitingResponse = false }) {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef(null)
  const prevMsgCount = useRef(conversation?.messages?.length || 0)

  useEffect(() => {
    prevMsgCount.current = conversation?.messages?.length || 0
  }, [conversation?.id])

  // Scroll when new messages arrive or when loading state appears (typing indicator)
  useEffect(() => {
    const count = conversation?.messages?.length || 0
    const newMessage = prevMsgCount.current > 0 && count > prevMsgCount.current
    prevMsgCount.current = count
    if (newMessage || isAwaitingResponse) {
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      })
    }
  }, [conversation?.messages?.length, isAwaitingResponse])

  const handleSend = () => {
    const text = inputValue.trim()
    if (!text || isAwaitingResponse) return
    onSendMessage?.(text)
    setInputValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!isAwaitingResponse) handleSend()
    }
  }

  // No conversation selected
  if (!conversation) {
    return (
      <div className="chat-panel">
        <div className="chat-panel__empty">
          <MessageCircle size={48} className="chat-panel__empty-icon" />
          <p className="chat-panel__empty-text">Kein Gespräch ausgewählt</p>
          <p className="chat-panel__empty-sub">
            Wähle ein Gespräch aus der Liste oder starte ein neues.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-panel">
      {/* ─── Header ─── */}
      <div className="chat-panel__header">
        <div className="chat-panel__header-left">
          <h2 className="chat-panel__title">{conversation.title}</h2>
          <p className="chat-panel__subtitle">
            <span>{conversation.subtitleParts?.[0]}</span>
            {conversation.subtitleParts?.slice(1).map((part, i) => (
              <React.Fragment key={i}>
                <span className="chat-panel__subtitle-dot" />
                <span>{part}</span>
              </React.Fragment>
            ))}
          </p>
        </div>
        <div className="chat-panel__header-actions">
          <button className="chat-panel__header-btn chat-panel__header-btn--primary">
            Exportieren
          </button>
          <button className="chat-panel__header-btn">Notiz speichern</button>
          <button className="chat-panel__header-btn">Teilen</button>
        </div>
      </div>

      {/* ─── Active Sources ─── */}
      {conversation.activeSources?.length > 0 && (
        <div className="chat-panel__sources">
          <span className="chat-panel__sources-label">Aktive Quellen:</span>
          <div className="chat-panel__sources-list">
            {conversation.activeSources.map(src => (
              <SourceTag key={src.id} label={src.label} type={src.type} />
            ))}
          </div>
        </div>
      )}

      {/* ─── Messages ─── */}
      <div className="chat-panel__messages">
        {conversation.dateDivider && (
          <div className="chat-panel__date-divider">
            <span className="chat-panel__date-label">{conversation.dateDivider}</span>
          </div>
        )}

        {conversation.messages.map(msg => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {isAwaitingResponse ? <ChatTypingIndicator /> : null}
        <div ref={messagesEndRef} />
      </div>

      {/* ─── Context bar ─── */}
      {conversation.contextTags?.length > 0 && (
        <div className="chat-panel__context-bar">
          <span className="chat-panel__context-icon">
            <Search size={14} />
            Kontext:
          </span>
          <div className="chat-panel__context-tags">
            {conversation.contextTags.map(tag => (
              <SourceTag key={tag.id} label={tag.label} type={tag.type} size="sm" />
            ))}
          </div>
        </div>
      )}

      {/* ─── Input ─── */}
      <div className="chat-panel__input-area">
        <div className="chat-panel__input-wrapper">
          <button className="chat-panel__add-btn" title="Kontext hinzufügen" aria-label="Kontext hinzufügen">
            <Plus size={14} />
          </button>
          <input
            type="text"
            className="chat-panel__input"
            placeholder="Weiter fragen oder neuen Kontext hinzufügen..."
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isAwaitingResponse}
            aria-busy={isAwaitingResponse}
            aria-label="Nachricht eingeben"
          />
        </div>
        <button
          className="chat-panel__send-btn"
          onClick={handleSend}
          disabled={!inputValue.trim() || isAwaitingResponse}
          title="Senden"
          aria-label="Nachricht senden"
        >
          <ArrowUp size={20} />
        </button>
      </div>
    </div>
  )
}
