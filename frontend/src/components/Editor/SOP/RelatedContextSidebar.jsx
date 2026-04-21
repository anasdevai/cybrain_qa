import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, ClipboardCheck, HelpCircle, Link, ShieldCheck } from 'lucide-react'

import { getRelatedContext } from '../../../api/editorApi'

const RelatedContextSidebar = ({ sopId, onLinkClick, refreshToken = 0 }) => {
  const [context, setContext] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchContext = useCallback(async () => {
    if (!sopId) {
      setContext(null)
      setError('')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await getRelatedContext(sopId)
      console.log('[RelatedContext] Fetched data for SOP:', sopId, data)
      setContext(data)
    } catch (err) {
      console.error('[RelatedContext] Failed to load data. SOP ID:', sopId, 'Error:', err)
      setContext(null)
      setError(err.message || 'Failed to load related context.')
    } finally {
      setLoading(false)
    }
  }, [sopId])

  useEffect(() => {
    fetchContext()
  }, [fetchContext, refreshToken])

  const sections = useMemo(() => ([
    {
      title: 'Linked SOPs',
      items: context?.related_sops || [],
      icon: <Link size={16} />,
      tone: 'sop',
      emptyText: 'No SOP chaining links found',
      getLabel: (item, index) =>
        item.title ||
        item.sop_number ||
        item.current_version?.metadata_json?.sopMetadata?.title ||
        `SOP ${index + 1}`,
      getStatus: (item) =>
        item.current_version?.external_status ||
        (item.is_active ? 'active' : 'inactive'),
    },
    {
      title: 'Deviations',
      items: context?.related_deviations || [],
      icon: <AlertTriangle size={16} />,
      tone: 'deviation',
      emptyText: 'No deviations linked',
      getLabel: (item, index) => item.title || item.deviation_number || `Deviation ${index + 1}`,
      getStatus: (item) => item.external_status || item.impact_level || 'open',
    },
    {
      title: 'CAPAs',
      items: context?.related_capas || [],
      icon: <ShieldCheck size={16} />,
      tone: 'capa',
      emptyText: 'No CAPAs linked',
      getLabel: (item, index) => item.title || item.capa_number || `CAPA ${index + 1}`,
      getStatus: (item) => item.external_status || item.effectiveness_status || 'open',
    },
    {
      title: 'Audit Findings',
      items: context?.related_audit_findings || [],
      icon: <ClipboardCheck size={16} />,
      tone: 'audit',
      emptyText: 'No audit findings linked',
      getLabel: (item, index) =>
        item.finding_number ||
        item.audit_number ||
        item.finding_text ||
        item.response_text ||
        item.authority ||
        `Audit finding ${index + 1}`,
      getStatus: (item) => item.acceptance_status || 'pending',
    },
    {
      title: 'Decisions',
      items: context?.related_decisions || [],
      icon: <HelpCircle size={16} />,
      tone: 'decision',
      emptyText: 'No decisions linked',
      getLabel: (item, index) => item.title || item.decision_number || `Decision ${index + 1}`,
      getStatus: (item) => item.decision_type || item.decided_by_role || 'decision',
    },
  ]), [context])

  if (!sopId) {
    return (
      <div className="sidebar-card">
        <div className="sidebar-section-kicker">Linked records</div>
        <h3 className="sidebar-title related-context-title">
          <Link size={18} />
          Linked QA Context
        </h3>
        <p className="context-empty-text">Save the SOP to view linked QA context.</p>
      </div>
    )
  }

  return (
    <section className="sidebar-card related-context-sidebar">
      <div className="sidebar-section-kicker">Linked records</div>
      <div className="related-context-header">
        <h3 className="related-context-title">
          <Link size={18} />
          Linked QA Context
        </h3>
        <button onClick={onLinkClick} className="add-link-btn">
          + Add Link
        </button>
      </div>

      <div className="related-context-content">
        {loading && (
          <div className="loading-context">
            <p>Loading related QA records...</p>
          </div>
        )}
        {error && (
          <div className="error-context">
            <p>{error}</p>
          </div>
        )}

        {!loading && (
          <div className="related-context-sections">
            {sections.map((section) => (
              <ContextSection
                key={section.title}
                title={section.title}
                items={section.items}
                icon={section.icon}
                tone={section.tone}
                emptyText={section.emptyText}
                getLabel={section.getLabel}
                getStatus={section.getStatus}
              />
            ))}
          </div>
        )}

      </div>
    </section>
  )
}

const ContextSection = ({ title, items, icon, tone, emptyText, getLabel, getStatus }) => {
  console.log(`[RelatedContext] Section '${title}' has ${items.length} items:`, items)
  return (
    <div className="context-section" data-type={title}>
      <h4 className="context-section-header">
        <span className={`context-section-icon ${tone}`}>{icon}</span>
        <span>{title}</span>
        <span className="context-section-count">{items.length}</span>
      </h4>
    {items.length === 0 ? (
      <p className="context-empty-text">{emptyText}</p>
    ) : (
      <div className="context-items-list">
        {items.map((item, index) => (
          <div key={item.id} className="context-item-card">
            <div className="context-item-label">{getLabel(item, index)}</div>
            <div className="context-item-status">
              {String(getStatus(item)).toLowerCase()}
            </div>
          </div>
        ))}
      </div>
      )}
    </div>
  )
}

export default RelatedContextSidebar
