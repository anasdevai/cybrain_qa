import { useLanguage } from '../../context/LanguageContext'

export default function SOPAuditTrail({ auditTrail = [] }) {
    const { t } = useLanguage()

    const labelMap = {
        draft: t.draft,
        under_review: t.underReview,
        effective: t.effective,
        obsolete: t.obsolete,
    }

    const getActionLabel = (entry) => {
        if (entry.action === 'created_new_revision') return t.newRevisionCreated
        return labelMap[entry.toStatus] || entry.action
    }

    return (
        <div className="contract-panel">
            <h3>{t.sopAuditTrail}</h3>

            {auditTrail.length === 0 ? (
                <p className="muted-text">{t.noAuditEntries}</p>
            ) : (
                <div className="review-comments-list">
                    {auditTrail
                        .slice()
                        .reverse()
                        .map((entry) => (
                            <div
                                key={entry.id || `${entry.createdAt}-${entry.action}`}
                                className="review-comment-item"
                            >
                                <p style={{ marginBottom: 6 }}>
                                    <strong>{getActionLabel(entry)}</strong>
                                </p>

                                {entry.action !== 'created_new_revision' && (entry.fromStatus || entry.toStatus) && (
                                    <p style={{ marginBottom: 6 }}>
                                        {entry.fromStatus ? (
                                            <>
                                                {t.from}: {labelMap[entry.fromStatus] || entry.fromStatus}
                                                {' -> '}
                                            </>
                                        ) : null}
                                        {t.to}: {labelMap[entry.toStatus] || entry.toStatus}
                                    </p>
                                )}
                                {entry.note ? (
                                    <p style={{ marginBottom: 6 }}>{entry.note}</p>
                                ) : null}

                                <small>
                                    {t.author}: {entry.actor || t.systemActor} ·{' '}
                                    {entry.createdAt
                                        ? new Date(entry.createdAt).toLocaleString()
                                        : ''}
                                </small>
                            </div>
                        ))}
                </div>
            )}
        </div>
    )
}