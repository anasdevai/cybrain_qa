/**
 * contractConstants.js
 * 
 * Centralized constant definitions used throughout the application to maintain
 * consistency in workflow states, labels, default profiles, and initial placeholder structures.
 */

// Available application personas/profiles that alter UI visibility
export const PROFILE_TYPES = {
    CONTRACT: 'contract',
    SOP: 'sop',
}

// Fixed constant strings representing the contract's review timeline
export const WORKFLOW_STATES = {
    DRAFT: 'draft',
    UNDER_REVIEW: 'under_review',
    CHANGES_REQUESTED: 'changes_requested',
    ACCEPTED: 'accepted',
    REJECTED: 'rejected',
}

// User-friendly display names for each workflow state
export const WORKFLOW_LABELS = {
    [WORKFLOW_STATES.DRAFT]: 'Draft',
    [WORKFLOW_STATES.UNDER_REVIEW]: 'Under Review',
    [WORKFLOW_STATES.CHANGES_REQUESTED]: 'Changes Requested',
    [WORKFLOW_STATES.ACCEPTED]: 'Accepted',
    [WORKFLOW_STATES.REJECTED]: 'Rejected',
}

// Common variables pre-loaded into the suggestion dropdown
export const DEFAULT_PLACEHOLDERS = [
    'ClientName',
    'Address',
    'Date',
    'Amount',
]

// The initial key-value state for common variables before the user provides data
export const CONTRACT_DEFAULT_VARIABLES = {
    ClientName: '',
    Address: '',
    Date: '',
    Amount: '',
}