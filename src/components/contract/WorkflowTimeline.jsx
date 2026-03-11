import { WORKFLOW_LABELS, WORKFLOW_STATES } from '../../utils/contractConstants'

const steps = [
    WORKFLOW_STATES.DRAFT,
    WORKFLOW_STATES.UNDER_REVIEW,
    WORKFLOW_STATES.CHANGES_REQUESTED,
    WORKFLOW_STATES.ACCEPTED,
    WORKFLOW_STATES.REJECTED,
]

export default function WorkflowTimeline({ workflowStatus }) {
    return (
        <div className="contract-panel">
            <h3>Workflow</h3>

            <div className="workflow-list">
                {steps.map((step) => {
                    const isActive = workflowStatus === step

                    return (
                        <div key={step} className={`workflow-item ${isActive ? 'active' : ''}`}>
                            <div className="workflow-dot" />
                            <span>{WORKFLOW_LABELS[step]}</span>
                            {isActive && <span className="current-badge">Current</span>}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}