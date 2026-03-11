import { useState } from 'react'
import { WORKFLOW_STATES } from '../utils/contractConstants'

export default function useWorkflowState(initialState = WORKFLOW_STATES.DRAFT) {
    const [workflowStatus, setWorkflowStatus] = useState(initialState)

    const setDraft = () => setWorkflowStatus(WORKFLOW_STATES.DRAFT)
    const setUnderReview = () => setWorkflowStatus(WORKFLOW_STATES.UNDER_REVIEW)
    const setChangesRequested = () => setWorkflowStatus(WORKFLOW_STATES.CHANGES_REQUESTED)
    const setAccepted = () => setWorkflowStatus(WORKFLOW_STATES.ACCEPTED)
    const setRejected = () => setWorkflowStatus(WORKFLOW_STATES.REJECTED)

    const isDraft = workflowStatus === WORKFLOW_STATES.DRAFT
    const isUnderReview = workflowStatus === WORKFLOW_STATES.UNDER_REVIEW
    const isChangesRequested = workflowStatus === WORKFLOW_STATES.CHANGES_REQUESTED
    const isAccepted = workflowStatus === WORKFLOW_STATES.ACCEPTED
    const isRejected = workflowStatus === WORKFLOW_STATES.REJECTED

    return {
        workflowStatus,
        setWorkflowStatus,

        setDraft,
        setUnderReview,
        setChangesRequested,
        setAccepted,
        setRejected,

        isDraft,
        isUnderReview,
        isChangesRequested,
        isAccepted,
        isRejected,
    }
}