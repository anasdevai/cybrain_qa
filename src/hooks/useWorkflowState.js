/**
 * useWorkflowState.js
 * 
 * A custom React hook that tracks and manages the overarching approval state
 * of a contract document moving through a typical business lifecycle.
 */
import { useState } from 'react'
import { WORKFLOW_STATES } from '../utils/contractConstants'

/**
 * Hook to manage contract document workflow states.
 * 
 * @param {string} initialState - Optional initial state (defaults to DRAFT)
 * @returns {Object} Current state, setter functions, and boolean status flags
 */
export default function useWorkflowState(initialState = WORKFLOW_STATES.DRAFT) {
    // Top-level status representing current phase of the document
    const [workflowStatus, setWorkflowStatus] = useState(initialState)

    // Direct transition mechanisms
    const setDraft = () => setWorkflowStatus(WORKFLOW_STATES.DRAFT)
    const setUnderReview = () => setWorkflowStatus(WORKFLOW_STATES.UNDER_REVIEW)
    const setChangesRequested = () => setWorkflowStatus(WORKFLOW_STATES.CHANGES_REQUESTED)
    const setAccepted = () => setWorkflowStatus(WORKFLOW_STATES.ACCEPTED)
    const setRejected = () => setWorkflowStatus(WORKFLOW_STATES.REJECTED)

    // Convenience boolean evaluations for UI rendering conditions
    const isDraft = workflowStatus === WORKFLOW_STATES.DRAFT
    const isUnderReview = workflowStatus === WORKFLOW_STATES.UNDER_REVIEW
    const isChangesRequested = workflowStatus === WORKFLOW_STATES.CHANGES_REQUESTED
    const isAccepted = workflowStatus === WORKFLOW_STATES.ACCEPTED
    const isRejected = workflowStatus === WORKFLOW_STATES.REJECTED

    return {
        workflowStatus,
        setWorkflowStatus, // Expose raw setter if necessary bounds check logic lives above

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