import { Search, SlidersHorizontal, Mail, Bell } from 'lucide-react';

export default function TopHeader({ user, onProfileOpen }) {
  return (
    <header className="cq-topbar">
      <div className="tb-search-wrap">
        <Search size={15} className="tb-search-icon" />
        <input className="tb-search-input" placeholder="Suchen" />
        <SlidersHorizontal size={15} className="tb-filter-icon" />
      </div>

      <div className="tb-right">
        <button className="tb-icon-btn" aria-label="Nachrichten">
          <Mail size={18} />
        </button>
        <button className="tb-icon-btn" aria-label="Benachrichtigungen">
          <Bell size={18} />
        </button>
        <button className="tb-avatar-btn" onClick={onProfileOpen} aria-label="Profil öffnen">
          <img src="/icons/user-avatar.svg" alt="Avatar" className="tb-avatar-img" />
        </button>
        <div className="tb-user-info">
          <span className="tb-user-name">{user?.username || 'Haider K.'}</span>
          <span className="tb-user-email">{user?.email || ''}</span>
        </div>
      </div>
    </header>
  );
}
