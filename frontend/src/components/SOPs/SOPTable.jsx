import React from 'react'
import { MoreVertical, FileText, ChevronRight, ExternalLink } from 'lucide-react'
import StatusBadge from '../Common/StatusBadge'

export default function SOPTable({ data, onRowClick, onOpenNewTab }) {
  return (
    <table className="sop-data-table">
      <thead>
        <tr>
          <th>Titel</th>
          <th>Code</th>
          <th>Version</th>
          <th>Status</th>
          <th>Letzte Änderung</th>
          <th>Verantwortlich</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {data.map((sop) => (
          <tr key={sop.id} className="sop-row" onClick={() => onRowClick?.(sop.id)}>
            <td className="title-cell">
              <div className="title-wrapper">
                <div className="file-icon">
                  <FileText size={18} />
                </div>
                <span>{sop.title}</span>
              </div>
            </td>
            <td className="code-cell">{sop.code}</td>
            <td className="version-cell">{sop.version}</td>
            <td className="status-cell">
              <StatusBadge status={sop.status} />
            </td>
            <td className="date-cell">{sop.date}</td>
            <td className="owner-cell">
              <div className="owner-avatar-group">
                <div className="owner-avatar-sm">
                  {sop.owner.charAt(0)}
                </div>
                <span>{sop.owner}</span>
              </div>
            </td>
            <td className="actions-cell">
              <button 
                className="row-action-btn-ghost"
                style={{ marginRight: '8px', border: 'none', background: 'transparent', cursor: 'pointer', color: '#667085' }}
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenNewTab?.(sop.id);
                }}
                title="In neuem Tab öffnen"
              >
                <ExternalLink size={16} />
              </button>
              <button className="row-action-btn">
                <ChevronRight size={18} />
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
