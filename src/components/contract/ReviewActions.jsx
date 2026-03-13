/**
 * ReviewActions.jsx
 * 
 * Renders a sidebar panel containing action buttons to progress
 * the document's review workflow state (e.g., Send for Review, Accept, Reject).
 */
import { useLanguage } from '../../context/LanguageContext'

/**
 * ReviewActions Component
 * 
 * @param {Object} props
 * @param {string} props.workflowStatus - Current status string for display.
 * @param {Function} props.setUnderReview - Workflow transition function.
 * @param {Function} props.setAccepted - Workflow transition function.
 * @param {Function} props.setChangesRequested - Workflow transition function.
 * @param {Function} props.setRejected - Workflow transition function.
 */
export default function ReviewActions({
    workflowStatus,
    setUnderReview,
    setAccepted,
    setChangesRequested,
    setRejected,
}) {
    const { t } = useLanguage()

    return (
        <div className="contract-panel">
            <h3>{t.clientReview}</h3>

            <p className="muted-text">
                {t.currentStatus}: {workflowStatus}
            </p>

            <div className="review-actions">
                <button
                    type="button"
                    onClick={setUnderReview}
                    className="primary-btn"
                >
                    {t.sendForReview}
                </button>

                <button
                    type="button"
                    onClick={setAccepted}
                    className="success-btn"
                >
                    {t.accept}
                </button>

                <button
                    type="button"
                    onClick={setChangesRequested}
                    className="warning-btn"
                >
                    {t.requestChanges}
                </button>

                <button
                    type="button"
                    onClick={setRejected}
                    className="danger-btn"
                >
                    {t.reject}
                </button>
            </div>
        </div>
    )
}