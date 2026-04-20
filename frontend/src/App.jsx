import { useState, useEffect, useRef, useMemo } from 'react';
import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import SessionsPanel from './components/SessionsPanel';
import ChatPanel from './components/ChatPanel';
import AuthScreen from './components/AuthScreen';
import ProfilePanel from './components/ProfilePanel';
import './index.css';

const API_URL = '/api';

const generateId = () =>
  'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || 'dev-token');
  const [user, setUser] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  // Cache citation tags per loaded session for display in the session list
  const [sessionTagsMap, setSessionTagsMap] = useState({});

  /* ── Auth ── */
  const handleLogin = async (tok) => {
    localStorage.setItem('token', tok);
    setToken(tok);
    try {
      const r = await fetch(`${API_URL}/auth/me`, { headers: { Authorization: `Bearer ${tok}` } });
      if (r.ok) setUser(await r.json());
    } catch (_) {}
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    if (token === 'dev-token') {
      setUser({ email: 'dev@example.com', username: 'Developer', role: 'admin' });
      return;
    }
    if (token && !user) {
      fetch(`${API_URL}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => (r.ok ? r.json() : null))
        .then(d => { if (d) setUser(d); else handleLogout(); })
        .catch(() => {});
    }
  }, [token]);

  /* ── Sessions ── */
  const loadSessions = async (tok) => {
    try {
      const res = await fetch(`${API_URL}/chat/sessions`, { headers: { Authorization: `Bearer ${tok}` } });
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        if (data.length > 0 && !activeSessionId) handleSelectSession(data[0].id, tok);
        if (data.length === 0) handleNewChat();
      }
    } catch (_) {}
  };

  useEffect(() => {
    if (token && user) loadSessions(token);
  }, [token, user]);

  const handleNewChat = () => {
    const id = generateId();
    setSessions(p => [{ id, title: 'Neues Gespräch', _isTemp: true }, ...p]);
    setActiveSessionId(id);
    setMessages([]);
  };

  const handleSelectSession = async (sid, tok = token) => {
    const s = sessions.find(x => x.id === sid);
    setActiveSessionId(sid);
    setMessages([]);
    if (!s?._isTemp) {
      try {
        const res = await fetch(`${API_URL}/chat/sessions/${sid}`, { headers: { Authorization: `Bearer ${tok}` } });
        if (res.ok) {
          const d = await res.json();
          const mapped = d.messages.map(m => ({
            role: m.role === 'assistant' ? 'bot' : 'user',
            id: m.id,
            text: m.content,
            citations: m.citations,
            suggestions: m.retrieval_metadata?.suggestions,
            retrieval_stats: m.retrieval_metadata?.stats,
            created_at: m.created_at,
          }));
          setMessages(mapped);
          // Cache tags from last bot message for the session list
          const lastBot = [...mapped].reverse().find(m => m.role === 'bot' && !m.error);
          if (lastBot?.citations?.length) {
            setSessionTagsMap(prev => ({
              ...prev,
              [sid]: lastBot.citations.filter(c => c.ref),
            }));
          }
        }
      } catch (_) {}
    }
  };

  const handleDeleteSession = async (sid) => {
    try {
      if (!sessions.find(s => s.id === sid)?._isTemp) {
        await fetch(`${API_URL}/chat/sessions/${sid}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } catch (_) {}
    setSessions(prev => {
      const f = prev.filter(s => s.id !== sid);
      if (sid === activeSessionId && f.length > 0) handleSelectSession(f[0].id);
      else if (f.length === 0) handleNewChat();
      return f;
    });
  };

  /* ── Send message ── */
  const send = async (queryText) => {
    const query = (queryText || input).trim();
    if (!query || loading) return;
    const userMsg = { role: 'user', id: generateId(), text: query };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput('');
    setLoading(true);

    try {
      let qid = activeSessionId;

      if (sessions.find(s => s.id === qid)?._isTemp) {
        try {
          const sRes = await fetch(`${API_URL}/chat/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({ title: query.substring(0, 40), collection_name: 'sops' }),
          });
          if (sRes.ok) {
            const sData = await sRes.json();
            qid = sData.id;
            setSessions(prev => [sData, ...prev.filter(x => x.id !== activeSessionId)]);
            setActiveSessionId(qid);
          }
        } catch (dbErr) { console.error('Session creation failed', dbErr); }
      }

      const resp = await fetch(`${API_URL}/query/smart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query, session_id: qid }),
      });

      if (resp.status === 401) { handleLogout(); throw new Error('Sitzung abgelaufen. Bitte erneut anmelden.'); }
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({ detail: `Serverfehler ${resp.status}` }));
        throw new Error(errData.detail || `Serverfehler ${resp.status}`);
      }

      const data = await resp.json();
      const botMsg = {
        role: 'bot',
        id: generateId(),
        text: data.answer,
        suggestions: data.suggestions || [],
        citations: data.citations || [],
        retrieval_stats: data.retrieval_stats,
      };
      setMessages([...next, botMsg]);

      // Cache tags for this session
      if (botMsg.citations?.length) {
        setSessionTagsMap(prev => ({
          ...prev,
          [qid]: botMsg.citations.filter(c => c.ref),
        }));
      }
    } catch (err) {
      let m = err.message;
      if (m === 'Failed to fetch') m = 'Verbindung unterbrochen. Bitte Backend prüfen.';
      setMessages([...next, { role: 'bot', id: generateId(), error: true, text: `Fehler: ${m}` }]);
    } finally {
      setLoading(false);
    }
  };

  /* ── Derived: active sources from last bot message ── */
  const activeSources = useMemo(() => {
    const lastBot = [...messages].reverse().find(m => m.role === 'bot' && !m.error);
    return (lastBot?.citations || []).filter(c => c.ref).slice(0, 6);
  }, [messages]);

  const activeSession = sessions.find(s => s.id === activeSessionId) || null;

  if (!token) return <AuthScreen onLogin={handleLogin} />;

  return (
    <div className="cq-app">
      {profileOpen && user && (
        <ProfilePanel
          user={user}
          token={token}
          onClose={() => setProfileOpen(false)}
          onProfileUpdated={setUser}
          onLogout={handleLogout}
        />
      )}

      <Sidebar onLogout={handleLogout} />

      <div className="cq-main">
        <TopHeader user={user} onProfileOpen={() => setProfileOpen(true)} />

        <div className="cq-content">
          <SessionsPanel
            sessions={sessions}
            activeSessionId={activeSessionId}
            onNewChat={handleNewChat}
            onSelectSession={handleSelectSession}
            onDeleteSession={handleDeleteSession}
            sessionTagsMap={sessionTagsMap}
          />
          <ChatPanel
            session={activeSession}
            messages={messages}
            loading={loading}
            input={input}
            onInputChange={setInput}
            onSend={send}
            activeSources={activeSources}
            user={user}
          />
        </div>
      </div>
    </div>
  );
}
