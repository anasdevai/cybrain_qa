import React, { useState, useMemo } from 'react'
import { Plus, Search } from 'lucide-react'
import SourceTag from './SourceTag'
import './ConversationList.css'

/**
 * ConversationList — Sidebar panel showing grouped conversations.
 */
export default function ConversationList({
  conversations = [],
  activeId,
  onSelect,
  onNewConversation
}) {
  const [search, setSearch] = useState('')

  // Filter by search term
  const filtered = useMemo(() => {
    if (!search.trim()) return conversations
    const q = search.toLowerCase()
    return conversations.filter(c =>
      c.title.toLowerCase().includes(q) ||
      c.description.toLowerCase().includes(q) ||
      c.tags.some(t => t.label.toLowerCase().includes(q))
    )
  }, [conversations, search])

  // Group by date label
  const grouped = useMemo(() => {
    const groups = []
    let currentGroup = null

    filtered.forEach(conv => {
      if (conv.dateGroup !== currentGroup) {
        currentGroup = conv.dateGroup
        groups.push({ label: currentGroup, items: [] })
      }
      groups[groups.length - 1].items.push(conv)
    })

    return groups
  }, [filtered])

  return (
    <div className="conversation-list">
      <div className="conv-list__header">
        <h2 className="conv-list__title">Gespräche</h2>

        <button
          className="conv-list__new-btn"
          onClick={onNewConversation}
          aria-label="Neues Gespräch starten"
        >
          <Plus size={16} />
          Neues Gespräch starten
        </button>

        <div className="conv-list__search">
          <Search size={16} className="conv-list__search-icon" />
          <input
            type="text"
            className="conv-list__search-input"
            placeholder="Gespräche durchsuchen..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            aria-label="Gespräche durchsuchen"
          />
        </div>
      </div>

      <div className="conv-list__items">
        {grouped.length === 0 && (
          <p className="conv-list__empty">Keine Gespräche gefunden.</p>
        )}

        {grouped.map(group => (
          <div key={group.label}>
            <p className="conv-list__group-label">{group.label}</p>
            {group.items.map(conv => (
              <div
                key={conv.id}
                className={`conv-item${conv.id === activeId ? ' conv-item--active' : ''}`}
                onClick={() => onSelect(conv.id)}
                role="button"
                tabIndex={0}
                aria-label={`Gespräch: ${conv.title}`}
                onKeyDown={e => e.key === 'Enter' && onSelect(conv.id)}
              >
                <div className="conv-item__top-row">
                  <span
                    className={`conv-item__dot${conv.hasAlert ? '' : ' conv-item__dot--hidden'}`}
                    aria-hidden="true"
                  />
                  <h3 className="conv-item__title">{conv.title}</h3>
                  <span className="conv-item__time">{conv.time}</span>
                </div>

                {conv.description && (
                  <p className="conv-item__desc">{conv.description}</p>
                )}

                {conv.tags?.length > 0 && (
                  <div className="conv-item__tags">
                    {conv.tags.map(tag => (
                      <SourceTag
                        key={tag.id}
                        label={tag.label}
                        type={tag.type}
                        size="sm"
                        showDot={false}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
