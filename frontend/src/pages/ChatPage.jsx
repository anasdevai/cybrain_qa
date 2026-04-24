import React, { useCallback, useMemo, useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import ConversationList from '../components/Chat/ConversationList'
import ChatPanel from '../components/Chat/ChatPanel'
import { queryAI } from '../api/editorApi'
import './ChatPage.css'

const CHAT_STORAGE_KEY = 'chat_page_conversations_v1'
const CHAT_ACTIVE_STORAGE_KEY = 'chat_page_active_conversation_v1'

function toHtml(text) {
  if (!text) return '<p></p>'
  const escaped = String(text)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
  return `<p>${escaped.replaceAll('\n', '<br/>')}</p>`
}

function stripHtml(html) {
  return String(html || '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .trim()
}

function nowTime() {
  return new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

function createInitialConversation() {
  return {
    id: 'live-chat',
    title: 'Live Chatbot',
    description: 'Stelle eine Frage an den RAG-Chatbot',
    time: nowTime(),
    dateGroup: 'Heute',
    hasAlert: false,
    tags: [{ id: 'source-sops', label: 'SOPs', type: 'sop' }],
    messages: [
      {
        id: 'm-welcome',
        sender: 'ai',
        time: nowTime(),
        content: '<p>Chatbot ist verbunden. Stelle eine Frage zu SOPs, Abweichungen, CAPAs, Audits oder Entscheidungen.</p>',
        tags: [],
        showActions: false,
      },
    ],
    activeSources: [],
    contextTags: [],
  }
}

/**
 * ChatPage — integrated chatbot UI backed by real /api/ai/query endpoint.
 */
export default function ChatPage() {
  const [conversations, setConversations] = useState(() => {
    try {
      const raw = localStorage.getItem(CHAT_STORAGE_KEY)
      const parsed = raw ? JSON.parse(raw) : null
      return Array.isArray(parsed) && parsed.length > 0 ? parsed : [createInitialConversation()]
    } catch {
      return [createInitialConversation()]
    }
  })
  const [activeConvId, setActiveConvId] = useState(() => localStorage.getItem(CHAT_ACTIVE_STORAGE_KEY) || 'live-chat')
  const [showChat, setShowChat] = useState(false)
  const [isSending, setIsSending] = useState(false)

  React.useEffect(() => {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(conversations))
  }, [conversations])

  React.useEffect(() => {
    if (!activeConvId && conversations.length > 0) {
      setActiveConvId(conversations[0].id)
      return
    }
    if (!activeConvId) return
    const exists = conversations.some((c) => c.id === activeConvId)
    if (!exists && conversations.length > 0) {
      setActiveConvId(conversations[0].id)
      return
    }
    localStorage.setItem(CHAT_ACTIVE_STORAGE_KEY, activeConvId)
  }, [activeConvId, conversations])

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeConvId) || null,
    [conversations, activeConvId],
  )

  const handleSelect = useCallback((id) => {
    setActiveConvId(id)
    setShowChat(true) // On mobile, switch to chat view
  }, [])

  const handleBack = useCallback(() => {
    setShowChat(false)
  }, [])

  const handleNewConversation = useCallback(() => {
    const id = `conv-${Date.now()}`
    const next = {
      id,
      title: 'Neues Gespräch',
      description: 'Noch keine Nachrichten',
      time: nowTime(),
      dateGroup: 'Heute',
      hasAlert: false,
      tags: [],
      messages: [],
      activeSources: [],
      contextTags: [],
    }
    setConversations((prev) => [next, ...prev])
    setActiveConvId(id)
    setShowChat(true)
  }, [])

  const handleSendMessage = useCallback(
    async (text) => {
      if (!activeConvId || !text?.trim() || isSending) return
      setIsSending(true)

      const userMsg = {
        id: `u-${Date.now()}`,
        sender: 'user',
        time: nowTime(),
        content: toHtml(text.trim()),
        tags: [],
        showActions: false,
      }

      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConvId
            ? {
                ...c,
                messages: [...c.messages, userMsg],
                description: text.trim().slice(0, 80),
                time: nowTime(),
              }
            : c,
        ),
      )

      try {
        const chatHistoryPayload = [
          ...(activeConversation?.messages || []).map((msg) => ({
            role: msg.sender === 'ai' ? 'assistant' : 'user',
            content: stripHtml(msg.content),
          })),
          { role: 'user', content: text.trim() },
        ].filter((item) => item.content)

        const result = await queryAI(text.trim(), { chat_history: chatHistoryPayload })
        const sourceTags = (result.sources || []).slice(0, 5).map((s, idx) => ({
          id: `src-${Date.now()}-${idx}`,
          label: s.label || s.id || `Quelle ${idx + 1}`,
          type: (s.type || 'sop').toLowerCase(),
        }))
        const aiMsg = {
          id: `a-${Date.now()}`,
          sender: 'ai',
          time: nowTime(),
          content: toHtml(result.answer || 'Keine Antwort erhalten.'),
          tags: sourceTags,
          showActions: true,
        }
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeConvId
              ? {
                  ...c,
                  title: c.title === 'Neues Gespräch' ? text.trim().slice(0, 45) : c.title,
                  messages: [...c.messages, aiMsg],
                  activeSources: sourceTags,
                  contextTags: sourceTags.slice(0, 2),
                }
              : c,
          ),
        )
      } catch (err) {
        const errMsg = {
          id: `e-${Date.now()}`,
          sender: 'ai',
          time: nowTime(),
          content: toHtml(`Fehler beim Chatbot-Aufruf: ${err.message || 'Unbekannter Fehler'}`),
          tags: [],
          showActions: false,
        }
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeConvId
              ? { ...c, messages: [...c.messages, errMsg], hasAlert: true }
              : c,
          ),
        )
      } finally {
        setIsSending(false)
      }
    },
    [activeConvId, activeConversation?.messages, isSending],
  )

  const mobileClass = showChat ? 'chat-page--show-chat' : 'chat-page--show-list'

  return (
    <div className={`chat-page ${mobileClass}`}>
      <ConversationList
        conversations={conversations}
        activeId={activeConvId}
        onSelect={handleSelect}
        onNewConversation={handleNewConversation}
      />

      <div className="chat-page__detail">
        {showChat && (
          <button className="chat-page__back-btn" onClick={handleBack}>
            <ArrowLeft size={16} />
            Zurück zur Liste
          </button>
        )}
        <ChatPanel
          conversation={
            activeConversation
              ? {
                  ...activeConversation,
                  subtitleParts: [
                    activeConversation.messages?.length
                      ? `${activeConversation.messages.length} Nachrichten`
                      : 'Noch keine Nachrichten',
                    isSending ? 'Antwort wird generiert…' : 'Live verbunden',
                  ],
                  dateDivider: 'Heute',
                }
              : null
          }
          onSendMessage={handleSendMessage}
          isAwaitingResponse={isSending}
        />
      </div>
    </div>
  )
}
