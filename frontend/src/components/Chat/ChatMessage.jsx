import React from 'react'
import { Sparkles } from 'lucide-react'
import SourceTag from './SourceTag'
import './ChatMessage.css'

/**
 * ChatMessage — Single chat message bubble for AI or user.
 */
export default function ChatMessage({ message, userInitials = 'HK' }) {
  const isAI = message.sender === 'ai'

  return (
    <div className={`chat-msg chat-msg--${message.sender}`}>
      <div className="chat-msg__avatar" aria-hidden="true">
        {isAI ? <Sparkles size={16} /> : userInitials}
      </div>

      <div className="chat-msg__wrapper">
        <div className="chat-msg__bubble">
          <div
            className="chat-msg__content"
            dangerouslySetInnerHTML={{ __html: message.content }}
          />

          {message.tags?.length > 0 && (
            <div className="chat-msg__tags">
              {message.tags.map(tag => (
                <SourceTag
                  key={tag.id}
                  label={tag.label}
                  type={tag.type}
                  size="sm"
                />
              ))}
            </div>
          )}
        </div>

        {message.showActions && (
          <div className="chat-msg__actions">
            <button className="chat-msg__action-btn" title="Nachricht kopieren">Kopieren</button>
            <button className="chat-msg__action-btn" title="Exportieren">Exportieren</button>
            <button className="chat-msg__action-btn" title="SOP öffnen">SOP öffnen</button>
          </div>
        )}

        <span className="chat-msg__time">{message.time}</span>
      </div>
    </div>
  )
}
