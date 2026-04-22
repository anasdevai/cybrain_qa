/**
 * sopConstants.js
 *
 * Derives runtime constants from the SOP workflow config.
 * All exports are helper lookups — no business rules live here.
 *
 * Legacy exports (SOP_STATES, SOP_LABELS, SOP_ORDER, SOP_ACTIONS) are
 * preserved as config-derived wrappers so existing imports keep working.
 */
import sopWorkflowConfig from './sopWorkflowConfig'

// ── Config-derived helpers ──────────────────────────────────────────

/** Build a { DRAFT: 'draft', UNDER_REVIEW: 'under_review', ... } map from config */
export function getStatesMap(config = sopWorkflowConfig) {
    const map = {}
    for (const s of config.states) {
        map[s.id.toUpperCase()] = s.id
    }
    return map
}

/** Build a { draft: 'Draft', under_review: 'Under Review', ... } label map from config */
export function getLabelsMap(config = sopWorkflowConfig) {
    const map = {}
    for (const s of config.states) {
        map[s.id] = s.label
    }
    return map
}

/** Get ordered array of state IDs from config */
export function getStateOrder(config = sopWorkflowConfig) {
    return config.states.map((s) => s.id)
}

/** Get action IDs from config transitions */
export function getActionIds(config = sopWorkflowConfig) {
    const map = {}
    for (const key of Object.keys(config.transitions)) {
        map[key.toUpperCase()] = key
    }
    return map
}

/** Build default metadata object from config field definitions */
export function getDefaultMetadata(config = sopWorkflowConfig) {
    const meta = {}
    for (const field of config.metadataFields) {
        if (field.multiValue) {
            meta[field.key] = []
        } else if (field.type === 'date') {
            meta[field.key] = ''
        } else {
            meta[field.key] = ''
        }
    }
    // Always include references array
    if (!meta.references) meta.references = []
    return meta
}

// ── Legacy exports (derived from default config) ────────────────────
// These maintain backward compatibility with existing imports.

export const SOP_STATES = getStatesMap()

export const SOP_LABELS = getLabelsMap()

export const SOP_ORDER = getStateOrder()

export const SOP_ACTIONS = getActionIds()

export const DEFAULT_SOP_METADATA = getDefaultMetadata()

export const DEFAULT_SOP_VERSION_METADATA = {
    sopStatus: sopWorkflowConfig.initialState,
    sopMetadata: { ...DEFAULT_SOP_METADATA },
    auditTrail: [],
    versionNote: '',
    approvedBy: '',
    approvalSignature: '',
    replacementDocumentId: '',
    obsoleteReason: '',
}