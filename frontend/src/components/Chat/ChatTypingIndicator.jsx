import React from 'react'
import { Sparkles } from 'lucide-react'

/**
 * Left-aligned typing row shown while the assistant response is loading.
 * Matches the visual line of AI messages in ChatPanel.
 */
export default function ChatTypingIndicator() {
  return (
    <div
      className="chat-typing"
      role="status"
      aria-live="polite"
      aria-label="Antwort wird generiert"
    >
      <div className="chat-typing__avatar" aria-hidden>
        <Sparkles size={16} />
      </div>
      <div className="chat-typing__bubble">
        <span className="chat-typing__dot" />
        <span className="chat-typing__dot" />
        <span className="chat-typing__dot" />
        <span className="chat-typing__sr">Assistent antwortet…</span>
      </div>
    </div>
  )
}
