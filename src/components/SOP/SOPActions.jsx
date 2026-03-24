import { useMemo, useState } from 'react'
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
    const [note, setNote] = useState('')
    const [error, setError] = useState('')

    const allowedActions = useMemo(
        () => getAllowedSOPActions(sopStatus),
        [sopStatus]
    )

    const validateRequiredNote = (type, trimmed) => {
        if (
            (type === SOP_ACTIONS.SUBMIT_REVIEW || type === SOP_ACTIONS.MARK_OBSOLETE) &&
            !trimmed
        ) {
            setError('This action requires a note.')
            return false
        }

        setError('')
        return true
    }

    const runAction = (type) => {
        const trimmed = note.trim()

        if (!validateRequiredNote(type, trimmed)) return

        if (type === SOP_ACTIONS.SUBMIT_REVIEW) {
            onSubmitForReview?.(trimmed)
            setNote('')
            return
        }

        if (type === SOP_ACTIONS.APPROVE) {
            onApprove?.(trimmed)
            setNote('')
            return
        }

        if (type === SOP_ACTIONS.SEND_BACK) {
            onSendBackToDraft?.(trimmed)
            setNote('')
            return
        }

        if (type === SOP_ACTIONS.MARK_OBSOLETE) {
            onMarkObsolete?.(trimmed)
            setNote('')
        }
    }

    if (isClientReviewMode) {
        return (
            <div className="review-actions">
                <h3>SOP Actions</h3>
                <p className="muted-text">Read-only mode enabled.</p>
            </div>
        )
    }

    return (
        <div className="review-actions">
            <h3>SOP Actions</h3>

            <p>
                <strong>Current Status:</strong> {SOP_LABELS[sopStatus] || sopStatus}
            </p>

            <textarea
                value={note}
                onChange={(e) => {
                    setNote(e.target.value)
                    if (error) setError('')
                }}
                rows={4}
                placeholder="Add change summary / approval note / obsolete reason..."
                className="review-comment-box"
            />

            {error && (
                <p style={{ color: 'red', fontSize: '13px', marginTop: '6px' }}>
                    {error}
                </p>
            )}

            <div
                className="review-actions-buttons"
                style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}
            >
                {allowedActions.includes(SOP_ACTIONS.SUBMIT_REVIEW) && (
                    <button
                        type="button"
                        className="primary-btn"
                        onClick={() => runAction(SOP_ACTIONS.SUBMIT_REVIEW)}
                    >
                        Submit for Review
                    </button>
                )}

                {allowedActions.includes(SOP_ACTIONS.APPROVE) && (
                    <button
                        type="button"
                        className="success-btn"
                        onClick={() => runAction(SOP_ACTIONS.APPROVE)}
                    >
                        Approve
                    </button>
                )}

                {allowedActions.includes(SOP_ACTIONS.SEND_BACK) && (
                    <button
                        type="button"
                        className="warning-btn"
                        onClick={() => runAction(SOP_ACTIONS.SEND_BACK)}
                    >
                        Send Back to Draft
                    </button>
                )}

                {allowedActions.includes(SOP_ACTIONS.MARK_OBSOLETE) && (
                    <button
                        type="button"
                        className="danger-btn"
                        onClick={() => runAction(SOP_ACTIONS.MARK_OBSOLETE)}
                    >
                        Mark Obsolete
                    </button>
                )}
            </div>
        </div>
    )
}