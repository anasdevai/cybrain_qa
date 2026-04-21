import React from 'react'
import { Search, Filter, Mail, Bell, Menu, Sparkles } from 'lucide-react'
import './Topbar.css'

export default function Topbar({ onMenuToggle, showLogo = false, logoTitle = "AI-Law Editor" }) {
  return (
    <header className="topbar-container">
      <div className="topbar-left-section">
        {/* Hamburger — shown only on mobile (≤1024px) */}
        <button
          className="hamburger-btn"
          onClick={onMenuToggle}
          aria-label="Menü öffnen"
        >
          <Menu size={20} />
        </button>

        {showLogo && (
          <div className="topbar-brand">
            <div className="brand-logo">Δ</div>
            <h2 className="brand-title">{logoTitle}</h2>
          </div>
        )}
      </div>

      <div className="search-wrapper">
        <div className="search-input-group">
          <Search size={18} className="search-icon" />
          <input type="text" placeholder="Suchen" className="search-input" />
        </div>
        <button className="filter-btn">
          <Filter size={18} />
        </button>
      </div>

      <div className="topbar-actions">
        <button className="action-icon-btn">
          <Mail size={20} />
        </button>
        <button className="action-icon-btn">
          <Bell size={20} />
        </button>

        <div className="user-profile-summary">
          <div className="user-info">
            <p className="user-name">Haider K.</p>
            <p className="user-email">haider@cybrain.ai</p>
          </div>
          <div className="avatar-wrapper">
            <img
              src="/avatar.png"
              alt="Profile"
              className="user-avatar"
              onError={e => { e.currentTarget.style.display = 'none' }}
            />
            <span className="avatar-initials">HK</span>
          </div>
        </div>
      </div>
    </header>
  )
}
