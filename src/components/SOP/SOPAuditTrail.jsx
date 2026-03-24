import { SOP_LABELS } from '../../utils/sopConstants'

export default function SOPAuditTrail({ auditTrail = [] }) {
    return (
        <div className="review-actions">
            <h3>SOP Audit Trail</h3>

            {auditTrail.length === 0 ? (
                <p className="muted-text">No audit entries yet.</p>
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
                                    <strong>{SOP_LABELS[entry.toStatus] || entry.action}</strong>
                                </p>

                                <p style={{ marginBottom: 6 }}>
                                    {entry.fromStatus ? (
                                        <>
                                            From: {SOP_LABELS[entry.fromStatus] || entry.fromStatus}
                                            {' -> '}
                                        </>
                                    ) : null}
                                    To: {SOP_LABELS[entry.toStatus] || entry.toStatus}
                                </p>

                                {entry.note ? (
                                    <p style={{ marginBottom: 6 }}>{entry.note}</p>
                                ) : null}

                                <small>
                                    {entry.actor || 'System'} ·{' '}
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