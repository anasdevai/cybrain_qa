export default function ReviewActions({
    workflowStatus,
    setUnderReview,
    setAccepted,
    setChangesRequested,
    setRejected,
}) {
    return (
        <div className="contract-panel">
            <h3>Client Review</h3>

            <p className="muted-text">Current status: {workflowStatus}</p>

            <div className="review-actions">
                <button type="button" onClick={setUnderReview} className="primary-btn">
                    Send For Review
                </button>

                <button type="button" onClick={setAccepted} className="success-btn">
                    Accept
                </button>

                <button
                    type="button"
                    onClick={setChangesRequested}
                    className="warning-btn"
                >
                    Request Changes
                </button>

                <button type="button" onClick={setRejected} className="danger-btn">
                    Reject
                </button>
            </div>
        </div>
    )
}