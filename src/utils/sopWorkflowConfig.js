/**
 * sopWorkflowConfig.js
 *
 * Single source of truth for all SOP workflow rules.
 * Every lifecycle state, transition, required field, metadata definition,
 * and versioning behavior is defined here as data — not code.
 *
 * Why:
 *   Different organizations have different SOP lifecycles.
 *   By encoding rules as config, the same codebase can serve any client
 *   by swapping this one object (now from a file, later from an API).
 *
 * Usage:
 *   import sopWorkflowConfig from './sopWorkflowConfig'
 *   — or —
 *   const config = useSOPConfig()           // from context (future)
 */

const sopWorkflowConfig = {
    // ── Lifecycle States ────────────────────────────────────────────
    // id       → internal key used in code and persistence
    // label    → translation key (resolved via t[label])
    // editable → whether the editor content can be modified in this state
    states: [
        { id: 'draft', label: 'draft', editable: true },
        { id: 'under_review', label: 'underReview', editable: false },
        { id: 'effective', label: 'effective', editable: false },
        { id: 'obsolete', label: 'obsolete', editable: false },
    ],

    // ── Initial State ───────────────────────────────────────────────
    initialState: 'draft',

    // ── Transitions ─────────────────────────────────────────────────
    // Each key is an action ID.
    //
    //   from     → array of state IDs where this action button appears
    //   to       → the target state after this action succeeds
    //   label    → translation key for the button text
    //   style    → CSS class for the button
    //   fields   → extra inputs rendered when this action is available
    //              key      → field identifier / state key
    //              type     → input type (text, textarea, date, etc.)
    //              label    → translation key for placeholder
    //              required → whether the field must be non-empty to proceed
    //   requires → validation rules checked before the transition is allowed
    //              note              → boolean: is a note/summary required?
    //              metadata          → array of metadata field keys that must be filled
    //              referencesRequired → boolean: at least one reference needed?
    transitions: {
        submit_review: {
            from: ['draft'],
            to: 'under_review',
            label: 'submitForReview',
            style: 'primary-btn',
            fields: [],
            requires: {
                note: true,
                metadata: ['documentId', 'title', 'author', 'reviewer'],
            },
        },

        approve: {
            from: ['under_review'],
            to: 'effective',
            label: 'approve',
            style: 'success-btn',
            fields: [
                {
                    key: 'approvalSignature',
                    type: 'text',
                    label: 'approvalSignature',
                    required: true,
                },
            ],
            requires: {
                metadata: ['documentId', 'title', 'author', 'reviewer'],
                referencesRequired: true,
            },
        },

        send_back: {
            from: ['under_review'],
            to: 'draft',
            label: 'sendBackToDraft',
            style: 'warning-btn',
            fields: [],
            requires: {},
        },

        mark_obsolete: {
            from: ['effective'],
            to: 'obsolete',
            label: 'markObsolete',
            style: 'danger-btn',
            fields: [
                {
                    key: 'replacementDocumentId',
                    type: 'text',
                    label: 'replacementDocumentId',
                    required: true,
                },
            ],
            requires: {
                note: true,
            },
        },
    },

    // ── Versioning ──────────────────────────────────────────────────
    // mode                → 'same_document' keeps versions in the same doc
    //                       'new_document_id' would create a separate document (future)
    // allowNewVersionFrom → states from which "New Version" is allowed
    // carryMetadata       → copy metadata to the new version
    // resetAuditTrail     → start a fresh audit trail for the new version
    versioning: {
        mode: 'same_document',
        allowNewVersionFrom: ['effective', 'obsolete'],
        carryMetadata: true,
        resetAuditTrail: true,
    },

    // ── Metadata Field Definitions ──────────────────────────────────
    // key        → field identifier used in the metadata object
    // type       → input type: 'text', 'date', 'textarea'
    // label      → translation key for placeholder / title
    // required   → whether the field shows a validation error when empty
    // multiValue → (optional) if true, value is an array split by separator
    // separator  → (optional) delimiter for multiValue fields
    metadataFields: [
        { key: 'documentId', type: 'text', label: 'documentId', required: true },
        { key: 'title', type: 'text', label: 'title', required: true },
        { key: 'department', type: 'text', label: 'department', required: false },
        { key: 'author', type: 'text', label: 'author', required: true },
        { key: 'reviewer', type: 'text', label: 'reviewer', required: true },
        { key: 'effectiveDate', type: 'date', label: 'effectiveDate', required: false },
        { key: 'reviewDate', type: 'date', label: 'reviewDate', required: false },
        { key: 'riskLevel', type: 'text', label: 'riskLevel', required: false },
        {
            key: 'regulatoryReferences',
            type: 'textarea',
            label: 'regulatoryReferences',
            required: false,
            multiValue: true,
            separator: '\n',
        },
    ],
}

export default sopWorkflowConfig

// ── Helpers ─────────────────────────────────────────────────────────────

/**
 * Deep-merge a base config with partial overrides.
 * Useful for client-specific tweaks or backend-provided patches.
 */
export function mergeConfig(base, overrides) {
    if (!overrides) return base
    return {
        ...base,
        ...overrides,
        states: overrides.states || base.states,
        transitions: overrides.transitions
            ? { ...base.transitions, ...overrides.transitions }
            : base.transitions,
        versioning: overrides.versioning
            ? { ...base.versioning, ...overrides.versioning }
            : base.versioning,
        metadataFields: overrides.metadataFields || base.metadataFields,
    }
}
