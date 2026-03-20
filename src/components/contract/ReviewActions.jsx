/**
 * ReviewActions.jsx
 * 
 * Renders a sidebar panel containing action buttons and comments
 * to manage the document's review workflow per version.
 */
import { useState } from 'react'
import { useLanguage } from '../../context/LanguageContext'

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

    const handleAddComment = () => {
        if (!commentText.trim()) return
        onAddComment?.(commentText.trim())
        setCommentText('')
    }

    return (
        <div className="contract-panel">
            <h3>{t.clientReview}</h3>

            <p className="muted-text">
                {t.currentStatus}: {workflowStatus}
            </p>

            {sentForReviewAt ? (
                <p className="muted-text">
                    Sent for review: {new Date(sentForReviewAt).toLocaleString()}
                </p>
            ) : null}

            <div className="review-actions">
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

            <div className="review-comments-section">
                <h4>Comments</h4>

                <textarea
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder="Add review comment..."
                    rows={4}
                />

                <button
                    type="button"
                    onClick={handleAddComment}
                    className="primary-btn"
                >
                    Add Comment
                </button>

                <div className="review-comments-list">
                    {reviewComments.length === 0 ? (
                        <p className="muted-text">No review comments yet.</p>
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