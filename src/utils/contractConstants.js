export const PROFILE_TYPES = {
    CONTRACT: 'contract',
    SOP: 'sop',
}

export const WORKFLOW_STATES = {
    DRAFT: 'draft',
    UNDER_REVIEW: 'under_review',
    CHANGES_REQUESTED: 'changes_requested',
    ACCEPTED: 'accepted',
    REJECTED: 'rejected',
}

export const WORKFLOW_LABELS = {
    [WORKFLOW_STATES.DRAFT]: 'Draft',
    [WORKFLOW_STATES.UNDER_REVIEW]: 'Under Review',
    [WORKFLOW_STATES.CHANGES_REQUESTED]: 'Changes Requested',
    [WORKFLOW_STATES.ACCEPTED]: 'Accepted',
    [WORKFLOW_STATES.REJECTED]: 'Rejected',
}

export const DEFAULT_PLACEHOLDERS = [
    'ClientName',
    'Address',
    'Date',
    'Amount',
]

export const CONTRACT_DEFAULT_VARIABLES = {
    ClientName: '',
    Address: '',
    Date: '',
    Amount: '',
}