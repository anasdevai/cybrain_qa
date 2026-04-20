import {
  LayoutGrid, FileText, Search, MessageSquare,
  AlertTriangle, Scale, ClipboardList, Network,
  Settings, HelpCircle, LogOut, PanelLeft
} from 'lucide-react';

const NAV_MAIN = [
  { icon: LayoutGrid, label: 'Start' },
  { icon: FileText, label: 'SOPs' },
  { icon: Search, label: 'Wissenssuche' },
  { icon: MessageSquare, label: 'Gespräche', active: true },
];

const NAV_QUALITY = [
  { icon: AlertTriangle, label: 'Abweichungen', badge: 3 },
  { icon: Scale, label: 'CAPA Maßnahmen' },
  { icon: ClipboardList, label: 'Audit Findings' },
  { icon: Network, label: 'Entscheidungen' },
];

const NAV_BOTTOM = [
  { icon: Settings, label: 'Einstellungen' },
  { icon: HelpCircle, label: 'Helfen' },
  { icon: LogOut, label: 'Abmelden', action: 'logout' },
];

export default function Sidebar({ onLogout }) {
  return (
    <aside className="cq-sidebar">
      <div className="sb-logo-row">
        <span className="sb-logo-text">Cybrain QS</span>
        <PanelLeft size={18} className="sb-logo-icon" />
      </div>

      <nav className="sb-nav">
        <p className="sb-section-label">Hauptmenü</p>
        {NAV_MAIN.map(({ icon: Icon, label, active }) => (
          <button
            key={label}
            className={`sb-nav-item ${active ? 'sb-nav-item--active' : ''}`}
          >
            <Icon size={16} />
            <span>{label}</span>
          </button>
        ))}

        <div className="sb-divider" />

        <p className="sb-section-label">Qualität</p>
        {NAV_QUALITY.map(({ icon: Icon, label, badge }) => (
          <button key={label} className="sb-nav-item">
            <Icon size={16} />
            <span className="sb-nav-label">{label}</span>
            {badge && <span className="sb-badge">{badge}</span>}
          </button>
        ))}
      </nav>

      <div className="sb-bottom">
        {NAV_BOTTOM.map(({ icon: Icon, label, action }) => (
          <button
            key={label}
            className="sb-nav-item sb-nav-item--bottom"
            onClick={action === 'logout' ? onLogout : undefined}
          >
            <Icon size={16} />
            <span>{label}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}
