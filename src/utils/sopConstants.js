export const SOP_STATES = {
    DRAFT: 'draft',
    UNDER_REVIEW: 'under_review',
    EFFECTIVE: 'effective',
    OBSOLETE: 'obsolete',
}

export const SOP_LABELS = {
    [SOP_STATES.DRAFT]: 'Draft',
    [SOP_STATES.UNDER_REVIEW]: 'Under Review',
    [SOP_STATES.EFFECTIVE]: 'Effective',
    [SOP_STATES.OBSOLETE]: 'Obsolete',
}

export const SOP_ORDER = [
    SOP_STATES.DRAFT,
    SOP_STATES.UNDER_REVIEW,
    SOP_STATES.EFFECTIVE,
    SOP_STATES.OBSOLETE,
]

export const SOP_ACTIONS = {
    SUBMIT_REVIEW: 'submit_review',
    APPROVE: 'approve',
    SEND_BACK: 'send_back',
    MARK_OBSOLETE: 'mark_obsolete',
}

export const DEFAULT_SOP_METADATA = {
    documentId: '',
    title: '',
    department: '',
    author: '',
    reviewer: '',
    effectiveDate: '',
    reviewDate: '',
    riskLevel: '',
    regulatoryReferences: [],
    references: [],
}

export const DEFAULT_SOP_VERSION_METADATA = {
    sopStatus: SOP_STATES.DRAFT,
    sopMetadata: { ...DEFAULT_SOP_METADATA },
    auditTrail: [],
    versionNote: '',
    approvedBy: '',
    approvalSignature: '',
    replacementDocumentId: '',
    obsoleteReason: '',
}