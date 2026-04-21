import React from 'react'
import { Bot, X } from 'lucide-react'
import './FloatingAskAIButton.css'

/**
 * FloatingAskAIButton — Toggles the AI widget drawer on mobile/tablet.
 * On desktop (>1024px) the AI widget is always visible in the grid,
 * so this button is hidden.
 */
export default function FloatingAskAIButton({ onClick, isOpen = false }) {
  return (
    <button
      className={`floating-ask-ai-btn${isOpen ? ' floating-ask-ai-btn--active' : ''}`}
      onClick={onClick}
      aria-label={isOpen ? 'KI Assistent schließen' : 'KI Assistent öffnen'}
    >
      {isOpen ? <X size={20} /> : <Bot size={20} />}
      <span>{isOpen ? 'Schließen' : 'Ask AI'}</span>
    </button>
  )
}
