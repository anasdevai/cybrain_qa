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
    const [approvalSignature, setApprovalSignature] = useState('')
    const [replacementDocumentId, setReplacementDocumentId] = useState('')
    const [error, setError] = useState('')

    const allowedActions = useMemo(
        () => getAllowedSOPActions(sopStatus),
        [sopStatus]
    )

    const statusLabelMap = {
        [SOP_LABELS.draft]: t.draft,
        [SOP_LABELS.under_review]: t.underReview,
        [SOP_LABELS.effective]: t.effective,
        [SOP_LABELS.obsolete]: t.obsolete,
        draft: t.draft,
        under_review: t.underReview,
        effective: t.effective,
        obsolete: t.obsolete,
    }

    const displayStatus =
        statusLabelMap[sopStatus] || SOP_LABELS[sopStatus] || sopStatus

    const runAction = async (type) => {
        let result = { ok: true }

        if (type === SOP_ACTIONS.SUBMIT_REVIEW) {
            result = await onSubmitForReview?.(note.trim())
        }

        if (type === SOP_ACTIONS.APPROVE) {
            result = await onApprove?.({
                note: note.trim(),
                approvalSignature: approvalSignature.trim(),
            })
        }

        if (type === SOP_ACTIONS.SEND_BACK) {
            result = await onSendBackToDraft?.(note.trim())
        }

        if (type === SOP_ACTIONS.MARK_OBSOLETE) {
            result = await onMarkObsolete?.({
                note: note.trim(),
                replacementDocumentId: replacementDocumentId.trim(),
            })
        }

        if (result?.ok === false) {
            setError(result.error || t.noteRequired)
            return
        }

        setError('')
        setNote('')
        setApprovalSignature('')
        setReplacementDocumentId('')
    }

    if (isClientReviewMode) {
        return (
            <div className="review-actions">
                <h3>{t.sopActions}</h3>
                <p className="muted-text">{t.readOnlyModeEnabled}</p>
            </div>
        )
    }

    return (
        <div className="review-actions">
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

            {allowedActions.includes(SOP_ACTIONS.APPROVE) && (
                <input
                    type="text"
                    value={approvalSignature}
                    onChange={(e) => setApprovalSignature(e.target.value)}
                    placeholder={t.approvalSignature}
                />
            )}

            {allowedActions.includes(SOP_ACTIONS.MARK_OBSOLETE) && (
                <input
                    type="text"
                    value={replacementDocumentId}
                    onChange={(e) => setReplacementDocumentId(e.target.value)}
                    placeholder={t.replacementDocumentId}
                />
            )}

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