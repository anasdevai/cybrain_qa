import { useState } from 'react'
import { useLanguage } from '../../../context/LanguageContext'

export default function ReviewLinkPanel({
    isClientReviewMode,
    reviewLink,
    onGenerateReviewLink,
}) {
    const { t } = useLanguage()
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
                <h3>{t.clientReviewMode}</h3>
                <p className="muted-text">
                    {t.sharedReviewReadonly}
                </p>
            </div>
        )
    }

    return (
        <div className="contract-panel">
            <h3>{t.shareReviewLink}</h3>

            <button
                type="button"
                onClick={onGenerateReviewLink}
                className="primary-btn"
            >
                {t.generateReviewLink}
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
                        className="secondary-btn copy-link-btn"
                    >
                        {copied ? t.copied : t.copyLink}
                    </button>
                </div>
            ) : null}
        </div>
    )
}
