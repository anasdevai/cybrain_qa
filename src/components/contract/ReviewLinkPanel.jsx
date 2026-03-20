import { useState } from 'react'

export default function ReviewLinkPanel({
    isClientReviewMode,
    reviewLink,
    onGenerateReviewLink,
}) {
    const [copied, setCopied] = useState(false)

    const handleCopy = async () => {
        if (!reviewLink) return

        try {
            await navigator.clipboard.writeText(reviewLink)
            setCopied(true)
            setTimeout(() => setCopied(false), 1500)
        } catch (error) {
            console.error('Copy failed:', error)
        }
    }

    if (isClientReviewMode) {
        return (
            <div className="contract-panel">
                <h3>Client Review Mode</h3>
                <p className="muted-text">
                    This document is opened through a shared review link and is read-only.
                </p>
            </div>
        )
    }

    return (
        <div className="contract-panel">
            <h3>Share Review Link</h3>

            <button
                type="button"
                onClick={onGenerateReviewLink}
                className="primary-btn"
            >
                Generate Review Link
            </button>

            {reviewLink ? (
                <div className="review-link-box">
                    <input
                        type="text"
                        value={reviewLink}
                        readOnly
                        className="review-link-input"
                    />

                    <button
                        type="button"
                        onClick={handleCopy}
                        className="secondary-btn"
                    >
                        {copied ? 'Copied' : 'Copy Link'}
                    </button>
                </div>
            ) : null}
        </div>
    )
}