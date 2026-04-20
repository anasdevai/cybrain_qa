import { useState } from 'react';

const API_URL = '/api';

export default function AuthScreen({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      if (isRegister) {
        if (password !== confirmPassword) throw new Error('Passwörter stimmen nicht überein.');
        const res = await fetch(`${API_URL}/auth/register`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, username, password, confirm_password: confirmPassword }),
        });
        if (!res.ok) {
          const dat = await res.json();
          let msg = dat.detail || 'Registrierung fehlgeschlagen';
          if (Array.isArray(msg)) msg = msg[0].msg.replace('Value error, ', '');
          throw new Error(msg);
        }
        setIsRegister(false); setError('Registriert! Bitte anmelden.');
      } else {
        const res = await fetch(`${API_URL}/auth/login`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
          const dat = await res.json();
          throw new Error(dat.detail || 'Ungültige E-Mail oder Passwort');
        }
        onLogin((await res.json()).access_token);
      }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-logo">
          <span className="auth-logo-text">Cybrain QS</span>
        </div>
        <h2 className="auth-heading">{isRegister ? 'Konto erstellen' : 'Anmelden'}</h2>
        <p className="auth-sub">{isRegister ? 'Neues Konto für Cybrain QS erstellen' : 'Sicher auf Ihr Qualitätssystem zugreifen'}</p>

        {error && (
          <div className={`auth-alert ${error.includes('Registriert') ? 'auth-alert--ok' : ''}`}>{error}</div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <label className="auth-label">E-Mail-Adresse</label>
          <input className="auth-input" type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="name@firma.de" />
          {isRegister && (
            <>
              <label className="auth-label">Benutzername</label>
              <input className="auth-input" type="text" value={username} onChange={e => setUsername(e.target.value)} required placeholder="Benutzername" />
            </>
          )}
          <label className="auth-label">Passwort</label>
          <input className="auth-input" type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" />
          {isRegister && (
            <>
              <label className="auth-label">Passwort bestätigen</label>
              <input className="auth-input" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required placeholder="••••••••" />
            </>
          )}
          <button className="auth-submit" disabled={loading}>
            {loading ? 'Bitte warten…' : (isRegister ? 'Konto erstellen' : 'Anmelden')}
          </button>
        </form>

        <p className="auth-switch">
          {isRegister ? 'Bereits ein Konto? ' : 'Noch kein Konto? '}
          <button className="auth-switch-btn" onClick={() => { setIsRegister(!isRegister); setError(''); }}>
            {isRegister ? 'Anmelden' : 'Registrieren'}
          </button>
        </p>
      </div>
    </div>
  );
}
