/**
 * WorkflowTimeline.jsx
 * 
 * Displays a visual timeline indicating the document's current position 
 * within the predefined contract review lifecycle (e.g., Draft -> Review -> Accepted).
 */
import { WORKFLOW_STATES } from '../../utils/contractConstants'
import { useLanguage } from '../../context/LanguageContext'

// Array defining the sequential order of workflow steps
const steps = [
    WORKFLOW_STATES.DRAFT,
    WORKFLOW_STATES.UNDER_REVIEW,
    WORKFLOW_STATES.CHANGES_REQUESTED,
    WORKFLOW_STATES.ACCEPTED,
    WORKFLOW_STATES.REJECTED,
]

/**
 * WorkflowTimeline Component
 * 
 * @param {Object} props
 * @param {string} props.workflowStatus - Current status string to highlight active step.
 */
export default function WorkflowTimeline({ workflowStatus }) {
    const { t } = useLanguage()

    const labels = {
        [WORKFLOW_STATES.DRAFT]: t.draft,
        [WORKFLOW_STATES.UNDER_REVIEW]: t.underReview,
        [WORKFLOW_STATES.CHANGES_REQUESTED]: t.changesRequested,
        [WORKFLOW_STATES.ACCEPTED]: t.accepted,
        [WORKFLOW_STATES.REJECTED]: t.rejected,
    }

    return (
        <div className="contract-panel">
            <h3>{t.workflow}</h3>

            <div className="workflow-list">
                {steps.map((step) => {
                    const isActive = workflowStatus === step

                    return (
                        <div
                            key={step}
                            className={`workflow-item ${isActive ? 'active' : ''}`}
                        >
                            <div className="workflow-dot" />
                            <span>{labels[step]}</span>
                            {isActive && <span className="current-badge">{t.current}</span>}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}