import { useRef, useEffect, useState } from 'react';
import { Plus, ArrowUp, Copy, Download, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatTime, getTagType, getTagPrefix } from '../utils/helpers';

/* ── Source chip pill ── */
function SourceChip({ citation, small }) {
  const type = getTagType(citation.ref, citation.type);
  const prefix = getTagPrefix(type);
  return (
    <span className={`src-chip src-chip--${type}${small ? ' src-chip--sm' : ''}`}>
      {prefix} {citation.ref}
    </span>
  );
}

/* ── Bot avatar circle ── */
function BotAvatar() {
  return (
    <div className="bot-avatar">
      <img src="/icons/bot-sparkle.svg" alt="" width={14} height={14} />
    </div>
  );
}

/* ── Date divider ── */
function DateDivider({ label }) {
  return (
    <div className="date-divider">
      <span className="date-divider-line" />
      <span className="date-divider-text">{label}</span>
      <span className="date-divider-line" />
    </div>
  );
}

/* ── Typing indicator ── */
function TypingBubble() {
  return (
    <div className="msg-bot-wrap">
      <BotAvatar />
      <div className="typing-bubble">
        <span /><span /><span />
      </div>
    </div>
  );
}

/* ── Bot message ── */
function BotMsg({ msg, onCopy, copiedId }) {
  const cits = (msg.citations || []).filter(c => c.ref);

  if (msg.error) {
    return (
      <div className="msg-bot-wrap">
        <BotAvatar />
        <div className="bot-bubble bot-bubble--error">{msg.text}</div>
      </div>
    );
  }

  return (
    <div className="msg-bot-wrap">
      <BotAvatar />
      <div className="bot-content">
        <div className="bot-bubble">
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
          </div>
          {cits.length > 0 && (
            <div className="msg-cits">
              {cits.slice(0, 6).map((c, i) => <SourceChip key={i} citation={c} small />)}
            </div>
          )}
        </div>
        <div className="bot-msg-footer">
          <div className="msg-actions">
            <button className="msg-action-btn" onClick={() => onCopy(msg.text, msg.id)}>
              {copiedId === msg.id ? 'Kopiert!' : 'Kopieren'}
            </button>
            <button className="msg-action-btn" onClick={() => onCopy(msg.text, `exp-${msg.id}`)}>
              Exportieren
            </button>
            <button className="msg-action-btn">SOP öffnen</button>
          </div>
          {msg.created_at && <span className="msg-time">{formatTime(msg.created_at)}</span>}
        </div>
      </div>
    </div>
  );
}

/* ── User message ── */
function UserMsg({ msg, initials }) {
  return (
    <div className="msg-user-wrap">
      <div className="user-bubble">{msg.text}</div>
      <div className="user-badge" aria-label="Nutzer">{initials}</div>
    </div>
  );
}

/* ── Welcome greeting ── */
function WelcomeMessage({ user }) {
  const name = user?.username?.split(' ')[0] || 'Haider';
  return (
    <div className="msg-bot-wrap">
      <BotAvatar />
      <div className="bot-bubble">
        <p>Guten Morgen, {name}. Ich bin bereit, Ihnen bei der Analyse von SOPs, Abweichungen, CAPAs und Audit-Befunden zu helfen. Womit soll ich beginnen?</p>
      </div>
    </div>
  );
}

/* ── Chat Panel ── */
export default function ChatPanel({
  session, messages, loading, input, onInputChange, onSend, activeSources, user
}) {
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const [copiedId, setCopiedId] = useState(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const userInitials = (user?.username || 'U').slice(0, 2).toUpperCase();

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const uniqueSources = [...new Set(activeSources.map(c => c.ref))].length;

  return (
    <div className="cq-chat-panel">
      {/* Header */}
      <div className="cp-header">
        <div className="cp-header-info">
          <h2 className="cp-title">{session?.title || 'Neues Gespräch'}</h2>
          <div className="cp-meta">
            {session?.updated_at && <span>{formatTime(session.updated_at)}</span>}
            {messages.length > 0 && <><span className="cp-dot">·</span><span>{messages.length} Nachrichten</span></>}
            {uniqueSources > 0 && <><span className="cp-dot">·</span><span>{uniqueSources} Quellen referenziert</span></>}
          </div>
        </div>
        <div className="cp-actions">
          <button className="cp-btn cp-btn--primary" onClick={() => handleCopy(messages.filter(m => m.role === 'bot').map(m => m.text).join('\n\n'), 'export')}>
            Exportieren
          </button>
          <button className="cp-btn">Notiz speichern</button>
          <button className="cp-btn">Teilen</button>
        </div>
      </div>

      {/* Active sources */}
      {activeSources.length > 0 && (
        <div className="cp-sources">
          <span className="cp-sources-label">Aktive Quellen:</span>
          <div className="cp-sources-row">
            {activeSources.map((c, i) => <SourceChip key={i} citation={c} />)}
          </div>
        </div>
      )}

      <div className="cp-divider" />

      {/* Messages */}
      <div className="cp-messages">
        {messages.length > 0 && <DateDivider label="Heute, 09:41" />}
        {messages.length === 0 && !loading && <WelcomeMessage user={user} />}

        {messages.map(m =>
          m.role === 'user'
            ? <UserMsg key={m.id} msg={m} initials={userInitials} />
            : <BotMsg key={m.id} msg={m} onCopy={handleCopy} copiedId={copiedId} />
        )}
        {loading && <TypingBubble />}
        <div ref={bottomRef} />
      </div>

      {/* Input dock */}
      <div className="cp-input-dock">
        {activeSources.length > 0 && (
          <div className="cp-ctx-row">
            <span className="cp-ctx-label">Kontext:</span>
            {activeSources.slice(0, 3).map((c, i) => <SourceChip key={i} citation={c} small />)}
          </div>
        )}
        <div className="cp-input-row">
          <button className="cp-add-btn" aria-label="Kontext hinzufügen">
            <Plus size={14} />
          </button>
          <textarea
            ref={inputRef}
            className="cp-textarea"
            value={input}
            onChange={e => onInputChange(e.target.value)}
            placeholder="Weiter fragen oder neuen Kontext hinzufügen…"
            rows={1}
            disabled={loading}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSend(); }
            }}
          />
          <button
            className="cp-send-btn"
            onClick={() => onSend()}
            disabled={loading || !input.trim()}
            aria-label="Senden"
          >
            {loading
              ? <span className="send-spinner" />
              : <ArrowUp size={14} />
            }
          </button>
        </div>
      </div>
    </div>
  );
}
