export const validateSOPMetadata = (metadata = {}) => {
    const errors = {}

    if (!metadata.documentId?.trim()) {
        errors.documentId = 'Document ID is required.'
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
            error: 'A review note is required before submitting for review.',
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

    return {
        ok: true,
        error: '',
        fieldErrors: {},
    }
}

export const canApproveSOP = ({ metadata = {}, references = [] }) => {
    const metadataErrors = validateSOPMetadata(metadata)

    if (Object.keys(metadataErrors).length > 0) {
        return {
            ok: false,
            error: 'Complete the required SOP metadata before approval.',
            fieldErrors: metadataErrors,
        }
    }

    if (!references?.length) {
        return {
            ok: false,
            error: 'At least one SOP reference is required before approval.',
            fieldErrors: {},
        }
    }

    return {
        ok: true,
        error: '',
        fieldErrors: {},
    }
}

export const canMarkSOPObsolete = ({ note = '' }) => {
    if (!note?.trim()) {
        return {
            ok: false,
            error: 'An obsolete reason is required.',
            fieldErrors: {},
        }
    }

    return {
        ok: true,
        error: '',
        fieldErrors: {},
    }
}