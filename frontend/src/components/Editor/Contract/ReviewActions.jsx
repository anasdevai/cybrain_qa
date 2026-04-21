import { useState } from 'react'
import { useLanguage } from '../../../context/LanguageContext'

export default function ReviewActions({
    workflowStatus,
    onSendForReview,
    onApprove,
    onRequestChanges,
    onReject,
    reviewComments = [],
    onAddComment,
    sentForReviewAt = null,
    isClientReviewMode = false,
}) {
    const { t } = useLanguage()
    const [commentText, setCommentText] = useState('')

    const statusLabelMap = {
        Draft: t.draft,
        'Under Review': t.underReview,
        'Changes Requested': t.changesRequested,
        Accepted: t.accepted,
        Rejected: t.rejected,
        draft: t.draft,
        under_review: t.underReview,
        changes_requested: t.changesRequested,
        accepted: t.accepted,
        rejected: t.rejected,
    }

    const displayStatus = statusLabelMap[workflowStatus] || workflowStatus

    const handleAddComment = () => {
        if (!commentText.trim()) return
        onAddComment?.(commentText.trim())
        setCommentText('')
    }

    return (
        <div className="contract-panel">
            <h3>{t.clientReview}</h3>

            <p className="muted-text">
                {t.currentStatus}: {displayStatus}
            </p>

            {sentForReviewAt ? (
                <p className="muted-text">
                    {t.sentForReview}: {new Date(sentForReviewAt).toLocaleString()}
                </p>
            ) : null}

            <div className="review-actions">
                <div className="review-actions-buttons">
                {!isClientReviewMode && (
                    <button
                        type="button"
                        onClick={onSendForReview}
                        className="primary-btn"
                    >
                        {t.sendForReview}
                    </button>
                )}

                <button
                    type="button"
                    onClick={onApprove}
                    className="success-btn"
                >
                    {t.accept}
                </button>

                <button
                    type="button"
                    onClick={onRequestChanges}
                    className="warning-btn"
                >
                    {t.requestChanges}
                </button>

                <button
                    type="button"
                    onClick={onReject}
                    className="danger-btn"
                >
                    {t.reject}
                </button>
                </div>
            </div>

            <div className="review-comments-section">
                <h4>{t.comments}</h4>

                <textarea
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder={t.addReviewComment}
                    rows={4}
                />

                <button
                    type="button"
                    onClick={handleAddComment}
                    className="primary-btn"
                >
                    {t.addComment}
                </button>

                <div className="review-comments-list">
                    {reviewComments.length === 0 ? (
                        <p className="muted-text">{t.noReviewComments}</p>
                    ) : (
                        reviewComments.map((comment, index) => (
                            <div
                                key={`${comment.createdAt || 'comment'}-${index}`}
                                className="review-comment-item"
                            >
                                <p>{comment.text}</p>
                                <small>
                                    {comment.createdAt
                                        ? new Date(comment.createdAt).toLocaleString()
                                        : ''}
                                </small>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    )
}
