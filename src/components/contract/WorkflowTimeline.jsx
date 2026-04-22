/**
 * WorkflowTimeline.jsx
 * 
 * Displays a visual timeline indicating the document's current position
 * within the predefined contract review lifecycle.
 */
import { WORKFLOW_ORDER, WORKFLOW_STATES } from '../../utils/contractConstants'
import { useLanguage } from '../../context/LanguageContext'

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

    const currentIndex = WORKFLOW_ORDER.indexOf(workflowStatus)

    return (
        <div className="contract-panel">
            <h3>{t.workflow}</h3>

            <div className="workflow-list">
                {WORKFLOW_ORDER.map((step, index) => {
                    const isActive = workflowStatus === step
                    const isCompleted = currentIndex >= index && currentIndex !== -1

                    return (
                        <div
                            key={step}
                            className={`workflow-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                        >
                            <div className="workflow-dot" />
                            <span>{labels[step] || step}</span>
                            {isActive && <span className="current-badge">{t.current}</span>}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}