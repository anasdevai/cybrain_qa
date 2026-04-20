import { useState } from 'react';
import { X } from 'lucide-react';

const API_URL = '/api';

export default function ProfilePanel({ user, token, onClose, onProfileUpdated, onLogout }) {
  const [username, setUsername] = useState(user?.username || '');
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  const save = async (e) => {
    e.preventDefault(); setMsg(null);
    if (newPw && newPw !== confirmPw) { setMsg({ type: 'error', text: 'Passwörter stimmen nicht überein.' }); return; }
    setSaving(true);
    const body = {};
    if (username.trim()) body.username = username.trim();
    if (newPw) { body.current_password = currentPw; body.new_password = newPw; }
    try {
      const res = await fetch(`${API_URL}/auth/me`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(body),
      });
      const dat = await res.json();
      if (!res.ok) throw new Error(Array.isArray(dat.detail) ? dat.detail[0].msg : dat.detail || 'Update fehlgeschlagen');
      onProfileUpdated(dat); setCurrentPw(''); setNewPw(''); setConfirmPw('');
      setMsg({ type: 'ok', text: 'Profil aktualisiert!' });
    } catch (err) { setMsg({ type: 'error', text: err.message }); }
    finally { setSaving(false); }
  };

  const initials = (user?.username || 'U').slice(0, 2).toUpperCase();

  return (
    <>
      <div className="pp-overlay" onClick={onClose} />
      <div className="pp-panel">
        <div className="pp-header">
          <h3 className="pp-heading">Profil & Einstellungen</h3>
          <button className="pp-close-btn" onClick={onClose} aria-label="Schließen"><X size={18} /></button>
        </div>

        <div className="pp-body">
          <div className="pp-identity">
            <div className="pp-avatar">{initials}</div>
            <div>
              <div className="pp-name">{user?.username}</div>
              <div className="pp-email">{user?.email}</div>
              <span className="pp-role">{user?.role || 'QS Mitarbeiter'}</span>
            </div>
          </div>

          <form className="pp-form" onSubmit={save}>
            {msg && <div className={`pp-msg pp-msg--${msg.type}`}>{msg.text}</div>}

            <p className="pp-section">Identität</p>
            <label className="auth-label">Anzeigename</label>
            <input className="auth-input" value={username} onChange={e => setUsername(e.target.value)} />
            <label className="auth-label">E-Mail</label>
            <input className="auth-input" value={user?.email || ''} disabled />

            <p className="pp-section">Passwort ändern</p>
            <label className="auth-label">Aktuelles Passwort</label>
            <input className="auth-input" type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)} placeholder="••••••••" />
            <label className="auth-label">Neues Passwort</label>
            <input className="auth-input" type="password" value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="••••••••" />
            <label className="auth-label">Passwort bestätigen</label>
            <input className="auth-input" type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} placeholder="••••••••" />

            <div className="pp-actions">
              <button className="pp-save-btn" type="submit" disabled={saving}>{saving ? 'Speichern…' : 'Speichern'}</button>
              <button className="pp-logout-btn" type="button" onClick={onLogout}>Abmelden</button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
