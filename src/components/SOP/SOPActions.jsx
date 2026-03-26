import { useMemo, useState } from 'react'
import { useLanguage } from '../../context/LanguageContext'
import {
    SOP_ACTIONS,
    SOP_LABELS,
} from '../../utils/sopConstants'
import { getAllowedSOPActions } from '../../utils/sopStateMachine'

export default function SOPActions({
    sopStatus,
    onSubmitForReview,
    onApprove,
    onSendBackToDraft,
    onMarkObsolete,
    isClientReviewMode = false,
}) {
    const { t } = useLanguage()
    const [note, setNote] = useState('')
    const [error, setError] = useState('')

    const allowedActions = useMemo(
        () => getAllowedSOPActions(sopStatus),
        [sopStatus]
    )

    const displayStatus = SOP_LABELS[sopStatus] || sopStatus

    const runAction = async (type) => {
        const trimmed = note.trim()
        let result = { ok: true }

        if (type === SOP_ACTIONS.SUBMIT_REVIEW) {
            result = await onSubmitForReview?.(trimmed)
        }

        if (type === SOP_ACTIONS.APPROVE) {
            result = await onApprove?.(trimmed)
        }

        if (type === SOP_ACTIONS.SEND_BACK) {
            result = await onSendBackToDraft?.(trimmed)
        }

        if (type === SOP_ACTIONS.MARK_OBSOLETE) {
            result = await onMarkObsolete?.(trimmed)
        }

        if (result?.ok === false) {
            setError(result.error || t.noteRequired)
            return
        }

        setError('')
        setNote('')
    }

    if (isClientReviewMode) {
        return (
            <div className="contract-panel">
                <h3>{t.sopActions}</h3>
                <p className="muted-text">{t.readOnlyModeEnabled}</p>
            </div>
        )
    }

    return (
        <div className="contract-panel">
            <h3>{t.sopActions}</h3>

            <p>
                <strong>{t.currentStatus}:</strong> {displayStatus}
            </p>

            <textarea
                value={note}
                onChange={(e) => {
                    setNote(e.target.value)
                    if (error) setError('')
                }}
                rows={4}
                placeholder={t.sopNotePlaceholder}
                className="review-comment-box"
            />

            {error && (
                <p style={{ color: 'red', fontSize: '13px', marginTop: '6px' }}>
                    {error}
                </p>
            )}

            <div
                className="review-actions-buttons"
            >
                {allowedActions.includes(SOP_ACTIONS.SUBMIT_REVIEW) && (
                    <button
                        type="button"
                        className="primary-btn"
                        onClick={() => runAction(SOP_ACTIONS.SUBMIT_REVIEW)}
                    >
                        {t.submitForReview}
                    </button>
                )}

                {allowedActions.includes(SOP_ACTIONS.APPROVE) && (
                    <button
                        type="button"
                        className="success-btn"
                        onClick={() => runAction(SOP_ACTIONS.APPROVE)}
                    >
                        {t.approve}
                    </button>
                )}

                {allowedActions.includes(SOP_ACTIONS.SEND_BACK) && (
                    <button
                        type="button"
                        className="warning-btn"
                        onClick={() => runAction(SOP_ACTIONS.SEND_BACK)}
                    >
                        {t.sendBackToDraft}
                    </button>
                )}

                {allowedActions.includes(SOP_ACTIONS.MARK_OBSOLETE) && (
                    <button
                        type="button"
                        className="danger-btn"
                        onClick={() => runAction(SOP_ACTIONS.MARK_OBSOLETE)}
                    >
                        {t.markObsolete}
                    </button>
                )}
            </div>
        </div>
    )
}