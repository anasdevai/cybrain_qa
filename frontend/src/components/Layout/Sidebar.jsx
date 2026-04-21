import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  Search, MessageCircle, LayoutDashboard,
  ClipboardList, AlertTriangle, Scale, FileText,
  GitBranch, Settings, HelpCircle, LogOut, Bot, X
} from 'lucide-react'
import { useSidebarCounts } from '../../hooks/useSidebarCounts'
import './Sidebar.css'

export default function Sidebar({ isOpen = false, onClose }) {
  const { sopCount, deviationCount } = useSidebarCounts()

  return (
    <aside className={`sidebar-container${isOpen ? ' sidebar-open' : ''}`}>
      {/* Mobile close button */}
      <button
        className="sidebar-close-btn"
        onClick={onClose}
        aria-label="Sidebar schließen"
      >
        <X size={18} />
      </button>

      <div className="sidebar-header">
        <div className="sidebar-brand">
          <h1 className="brand-logo">Cybrain QS</h1>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">
          <p className="section-label">Hauptmenü</p>
          <NavLink to="/" className="nav-link" end>
            <LayoutDashboard size={18} />
            <span className="nav-text">Start</span>
          </NavLink>
          <NavLink to="/sops" className="nav-link">
            <ClipboardList size={18} />
            <span className="nav-text">SOPs</span>
            {sopCount !== null && (
              <span className="nav-badge blue">{sopCount}</span>
            )}
          </NavLink>
          <NavLink to="/knowledge" className="nav-link">
            <Search size={18} />
            <span className="nav-text">Wissenssuche</span>
          </NavLink>
          <NavLink to="/chat" className="nav-link">
            <MessageCircle size={18} />
            <span className="nav-text">Gespräche</span>
          </NavLink>
        </div>

        <div className="nav-section">
          <p className="section-label">Qualität</p>
          <NavLink to="/deviations" className="nav-link">
            <AlertTriangle size={18} />
            <span className="nav-text">Abweichungen</span>
            {deviationCount !== null && (
              <span className="nav-badge red">{deviationCount}</span>
            )}
          </NavLink>
          <NavLink to="/capa" className="nav-link">
            <Scale size={18} />
            <span className="nav-text">CAPA Maßnahmen</span>
          </NavLink>
          <NavLink to="/audits" className="nav-link">
            <FileText size={18} />
            <span className="nav-text">Audit Findings</span>
          </NavLink>
          <NavLink to="/decisions" className="nav-link">
            <GitBranch size={18} />
            <span className="nav-text">Entscheidungen</span>
          </NavLink>
          <NavLink to="/chat" className="nav-link nav-link-ki">
            <Bot size={18} />
            <span className="nav-text">KI fragen</span>
          </NavLink>
        </div>
      </nav>

      <div className="sidebar-footer">
        <NavLink to="/settings" className="nav-link">
          <Settings size={18} />
          <span className="nav-text">Einstellungen</span>
        </NavLink>
        <NavLink to="/help" className="nav-link">
          <HelpCircle size={18} />
          <span className="nav-text">Helfen</span>
        </NavLink>
        <button className="nav-link logout-btn">
          <LogOut size={18} />
          <span className="nav-text">Abmelden</span>
        </button>
      </div>
    </aside>
  )
}
