import { useLanguage } from '../../../context/LanguageContext'

export default function SOPAuditTrail({ auditTrail = [], currentVersion }) {
  const { t } = useLanguage()

  const labelMap = {
    draft: t.draft,
    under_review: t.underReview,
    effective: t.effective,
    obsolete: t.obsolete,
  }

  const getActionLabel = (entry) => {
    if (entry.action === 'created_new_revision') return t.newRevisionCreated
    return labelMap[entry.toStatus] || entry.action || t.systemActor
  }

  return (
    <div className="sop-panel">
      <h3>{t.sopAuditTrail}</h3>

      {auditTrail.length === 0 ? (
        <p className="muted-text">{t.noAuditEntries}</p>
      ) : (
        <div className="sop-audit-list">
          {auditTrail
            .slice()
            .reverse()
            .map((entry, index) => (
              <div
                key={entry.id || `${entry.createdAt}-${entry.action}-${index}`}
                className={`sop-audit-item${index === 0 ? ' is-latest' : ''}`}
              >
                <div className="sop-audit-top">
                  <span className="sop-audit-version">
                    {entry.version ? `v${entry.version}` : currentVersion ? `v${currentVersion}` : 'v?'}
                  </span>
                  <span className="sop-audit-action">{getActionLabel(entry)}</span>
                </div>

                {(entry.fromStatus || entry.toStatus) && entry.action !== 'created_new_revision' ? (
                  <div className="sop-audit-transition">
                    {entry.fromStatus ? (
                      <span className="sop-audit-from">{labelMap[entry.fromStatus] || entry.fromStatus}</span>
                    ) : null}
                    {entry.fromStatus && entry.toStatus ? <span>{' -> '}</span> : null}
                    {entry.toStatus ? (
                      <span className="sop-audit-to">{labelMap[entry.toStatus] || entry.toStatus}</span>
                    ) : null}
                  </div>
                ) : null}

                {entry.note ? (
                  <p className="sop-audit-note">{entry.note}</p>
                ) : null}

                <div className="sop-audit-meta">
                  <span>{entry.actor || t.systemActor}</span>
                  <span>{entry.createdAt ? new Date(entry.createdAt).toLocaleDateString() : ''}</span>
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}
