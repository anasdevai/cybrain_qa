export const validateSOPMetadata = (metadata = {}) => {
    const errors = {}

    if (!metadata.documentId?.trim()) {
        errors.documentId = 'Document ID is required.'
    }

    if (!metadata.title?.trim()) {
        errors.title = 'Title is required.'
    }

    if (!metadata.author?.trim()) {
        errors.author = 'Author is required.'
    }

    if (!metadata.reviewer?.trim()) {
        errors.reviewer = 'Reviewer is required.'
    }

    return errors
}

export const canSubmitSOPForReview = ({ metadata = {}, note = '' }) => {
    const metadataErrors = validateSOPMetadata(metadata)

    if (!note?.trim()) {
        return {
            ok: false,
            error: 'A change summary is required before submitting for review.',
            fieldErrors: metadataErrors,
        }
    }

    if (Object.keys(metadataErrors).length > 0) {
        return {
            ok: false,
            error: 'Complete the required SOP metadata before submitting for review.',
            fieldErrors: metadataErrors,
        }
    }

    return { ok: true, error: '', fieldErrors: {} }
}

export const canApproveSOP = ({
    metadata = {},
    references = [],
    approvalSignature = '',
}) => {
    const metadataErrors = validateSOPMetadata(metadata)

    if (Object.keys(metadataErrors).length > 0) {
        return {
            ok: false,
            error: 'Complete the required SOP metadata before approval.',
            fieldErrors: metadataErrors,
        }
    }

    if (!references?.length && !metadata?.regulatoryReferences?.length) {
        return {
            ok: false,
            error: 'At least one reference or regulatory reference is required before approval.',
            fieldErrors: {},
        }
    }

    if (!approvalSignature?.trim()) {
        return {
            ok: false,
            error: 'Approval signature is required before marking the SOP as Effective.',
            fieldErrors: {},
        }
    }

    return { ok: true, error: '', fieldErrors: {} }
}

export const canMarkSOPObsolete = ({
    note = '',
    replacementDocumentId = '',
}) => {
    if (!note?.trim()) {
        return {
            ok: false,
            error: 'A reason is required before marking the SOP as Obsolete.',
            fieldErrors: {},
        }
    }

    if (!replacementDocumentId?.trim()) {
        return {
            ok: false,
            error: 'Replacement Document ID is required before marking the SOP as Obsolete.',
            fieldErrors: {},
        }
    }

    return { ok: true, error: '', fieldErrors: {} }
}