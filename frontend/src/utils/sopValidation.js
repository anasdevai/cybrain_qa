/**
 * sopValidation.js
 *
 * Config-driven SOP transition validation.
 *
 * Before: 3 hardcoded validation functions (canSubmitSOPForReview,
 *         canApproveSOP, canMarkSOPObsolete) with fixed required fields.
 *
 * After:  1 generic function — validateSOPTransition() — that reads
 *         required fields from config.transitions[actionId].
 *
 * Adding a new transition or changing required fields never requires
 * touching this file — only the config.
 */
import sopWorkflowConfig from './sopWorkflowConfig'

/**
 * Validate SOP metadata fields against a required list.
 * Only checks the fields listed — the list itself comes from config.
 *
 * @param {Object} metadata       - Current metadata values
 * @param {string[]} requiredKeys - Which metadata keys must be non-empty
 * @returns {Object} errors map   - { fieldKey: 'error message', ... }
 */
export function validateSOPMetadata(metadata = {}, requiredKeys = []) {
    const errors = {}

    for (const key of requiredKeys) {
        const value = metadata?.[key]

        // Arrays (like regulatoryReferences) — check length
        if (Array.isArray(value)) {
            if (value.length === 0) {
                errors[key] = `${key} is required.`
            }
        }
        // Strings — check non-empty after trim
        else if (!value?.toString().trim()) {
            errors[key] = `${key} is required.`
        }
    }

    return errors
}

/**
 * Generic SOP transition validator.
 * Reads all rules from config.transitions[actionId] and validates
 * the provided data against them.
 *
 * @param {string} actionId           - The transition action ID (e.g. 'submit_review')
 * @param {Object} data
 * @param {Object} data.metadata      - Current SOP metadata
 * @param {string} data.note          - Note / change summary text
 * @param {Object} data.actionFields  - Extra fields collected from the UI (e.g. { approvalSignature: '...' })
 * @param {Object} [config]           - Workflow config (defaults to static config)
 * @returns {{ ok: boolean, error: string, fieldErrors: Object }}
 */
export function validateSOPTransition(
    actionId,
    { metadata = {}, note = '', actionFields = {} },
    config = sopWorkflowConfig
) {
    const transition = config.transitions[actionId]

    if (!transition) {
        return { ok: false, error: `Unknown action: ${actionId}`, fieldErrors: {} }
    }

    const requires = transition.requires || {}
    const fieldErrors = {}

    // 1. Check note requirement
    if (requires.note && !note?.trim()) {
        return {
            ok: false,
            error: 'A note or summary is required for this action.',
            fieldErrors,
        }
    }

    // 2. Check required metadata fields
    if (requires.metadata && requires.metadata.length > 0) {
        const metaErrors = validateSOPMetadata(metadata, requires.metadata)

        if (Object.keys(metaErrors).length > 0) {
            return {
                ok: false,
                error: 'Complete the required SOP metadata before proceeding.',
                fieldErrors: metaErrors,
            }
        }
    }

    // 3. Check references requirement
    if (requires.referencesRequired) {
        const refs = [
            ...(metadata?.references || []),
            ...(metadata?.regulatoryReferences || []),
        ]

        if (refs.length === 0) {
            return {
                ok: false,
                error: 'At least one reference or regulatory reference is required.',
                fieldErrors: {},
            }
        }
    }

    // 4. Check action-specific extra fields (e.g. approvalSignature, replacementDocumentId)
    for (const field of transition.fields || []) {
        if (field.required && !actionFields?.[field.key]?.toString().trim()) {
            return {
                ok: false,
                error: `${field.label || field.key} is required.`,
                fieldErrors: {},
            }
        }
    }

    return { ok: true, error: '', fieldErrors: {} }
}

// ── Legacy wrappers ─────────────────────────────────────────────────
// These preserve backward compatibility with existing App.jsx imports.
// They delegate to validateSOPTransition under the hood.

export function canSubmitSOPForReview({ metadata = {}, note = '' }) {
    return validateSOPTransition('submit_review', { metadata, note })
}

export function canApproveSOP({
    metadata = {},
    references = [],
    approvalSignature = '',
}) {
    // Merge external references into metadata for the generic validator
    const enrichedMetadata = {
        ...metadata,
        references: [
            ...(metadata?.references || []),
            ...references.filter((r) => !(metadata?.references || []).includes(r)),
        ],
    }

    return validateSOPTransition('approve', {
        metadata: enrichedMetadata,
        actionFields: { approvalSignature },
    })
}

export function canMarkSOPObsolete({ note = '', replacementDocumentId = '' }) {
    return validateSOPTransition('mark_obsolete', {
        note,
        actionFields: { replacementDocumentId },
    })
}