import { Plus, Search, Trash2 } from 'lucide-react';
import { groupSessionsByDate, formatSessionTime, getSessionDotColor, getTagType, getTagPrefix } from '../utils/helpers';

function SessionTag({ citation }) {
  const type = getTagType(citation.ref, citation.type);
  const prefix = getTagPrefix(type);
  return (
    <span className={`sess-tag sess-tag--${type}`}>
      {prefix} {citation.ref}
    </span>
  );
}

function SessionItem({ session, isActive, onClick, onDelete, tags }) {
  const dotColor = getSessionDotColor(session);
  const time = formatSessionTime(session.updated_at || session.created_at);
  const preview = session.last_message || session.title || '';

  return (
    <div
      className={`sess-item ${isActive ? 'sess-item--active' : ''}`}
      onClick={onClick}
    >
      {isActive && <div className="sess-item-bar" />}
      <div className="sess-item-inner">
        <div className="sess-item-row">
          <div className="sess-item-title-row">
            <span className="sess-dot" style={{ background: dotColor }} />
            <span className="sess-title">{session.title || 'Neues Gespräch'}</span>
          </div>
          <span className="sess-time">{time}</span>
        </div>
        {preview && preview !== session.title && (
          <p className="sess-preview">{preview}</p>
        )}
        {tags && tags.length > 0 && (
          <div className="sess-tags">
            {tags.slice(0, 4).map((c, i) => <SessionTag key={i} citation={c} />)}
          </div>
        )}
      </div>
      <button
        className="sess-delete-btn"
        onClick={e => { e.stopPropagation(); onDelete(session.id); }}
        aria-label="Sitzung löschen"
      >
        <Trash2 size={12} />
      </button>
    </div>
  );
}

function SectionGroup({ label, sessions, activeSessionId, onSelectSession, onDeleteSession, sessionTagsMap }) {
  if (!sessions.length) return null;
  return (
    <>
      <p className="sess-group-label">{label}</p>
      {sessions.map(s => (
        <SessionItem
          key={s.id}
          session={s}
          isActive={s.id === activeSessionId}
          onClick={() => onSelectSession(s.id)}
          onDelete={onDeleteSession}
          tags={sessionTagsMap?.[s.id]}
        />
      ))}
    </>
  );
}

export default function SessionsPanel({
  sessions, activeSessionId, onNewChat, onSelectSession, onDeleteSession, sessionTagsMap
}) {
  const groups = groupSessionsByDate(sessions.filter(s => !s._isTemp));
  const tempSessions = sessions.filter(s => s._isTemp);

  return (
    <div className="cq-sessions-panel">
      <div className="sp-header">
        <h2 className="sp-title">Gespräche</h2>
      </div>

      <div className="sp-actions">
        <button className="sp-new-btn" onClick={onNewChat}>
          <Plus size={13} />
          <span>Neues Gespräch starten</span>
        </button>
      </div>

      <div className="sp-search-wrap">
        <Search size={12} className="sp-search-icon" />
        <input className="sp-search-input" placeholder="Gespräche durchsuchen…" />
      </div>

      <div className="sp-divider" />

      <div className="sp-list">
        {tempSessions.map(s => (
          <SessionItem
            key={s.id}
            session={s}
            isActive={s.id === activeSessionId}
            onClick={() => onSelectSession(s.id)}
            onDelete={onDeleteSession}
            tags={[]}
          />
        ))}
        {[...tempSessions, ...groups.heute, ...groups.gestern, ...groups.dieseWoche, ...groups.aelter].length === 0 && (
          <p className="sp-empty">Noch keine Gespräche</p>
        )}
        <SectionGroup label="Heute" sessions={groups.heute} activeSessionId={activeSessionId} onSelectSession={onSelectSession} onDeleteSession={onDeleteSession} sessionTagsMap={sessionTagsMap} />
        <SectionGroup label="Gestern" sessions={groups.gestern} activeSessionId={activeSessionId} onSelectSession={onSelectSession} onDeleteSession={onDeleteSession} sessionTagsMap={sessionTagsMap} />
        <SectionGroup label="Diese Woche" sessions={groups.dieseWoche} activeSessionId={activeSessionId} onSelectSession={onSelectSession} onDeleteSession={onDeleteSession} sessionTagsMap={sessionTagsMap} />
        <SectionGroup label="Älter" sessions={groups.aelter} activeSessionId={activeSessionId} onSelectSession={onSelectSession} onDeleteSession={onDeleteSession} sessionTagsMap={sessionTagsMap} />
      </div>
    </div>
  );
}
