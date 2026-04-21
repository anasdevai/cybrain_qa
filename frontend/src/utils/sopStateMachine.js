/**
 * sopStateMachine.js
 *
 * Config-driven SOP state machine.
 * All transition rules, allowed actions, and editability checks
 * are read from the workflow config — not hardcoded.
 */
import sopWorkflowConfig from './sopWorkflowConfig'

// ── Transition checks ───────────────────────────────────────────────

/**
 * Check whether a transition from one state to another is allowed.
 * Looks up config.transitions to find any action whose `from` includes
 * the current state and whose `to` matches the target state.
 */
export function canTransitionSOP(from, to, config = sopWorkflowConfig) {
    return Object.values(config.transitions).some(
        (t) => t.from.includes(from) && t.to === to
    )
}

// ── Editability ─────────────────────────────────────────────────────

/**
 * Check whether document content is editable in the given state.
 * Reads the `editable` flag from config.states.
 */
export function canEditSOP(status, config = sopWorkflowConfig) {
    const state = config.states.find((s) => s.id === status)
    return state?.editable ?? false
}

// ── Allowed actions ─────────────────────────────────────────────────

/**
 * Get the list of action IDs available for the current status.
 * Returns an array of action IDs (e.g. ['submit_review']).
 */
export function getAllowedSOPActions(status, config = sopWorkflowConfig) {
    return Object.entries(config.transitions)
        .filter(([, t]) => t.from.includes(status))
        .map(([actionId]) => actionId)
}

/**
 * Get full transition objects available for the current status.
 * Returns array of [actionId, transitionConfig] pairs.
 */
export function getAllowedTransitions(status, config = sopWorkflowConfig) {
    return Object.entries(config.transitions).filter(([, t]) =>
        t.from.includes(status)
    )
}

// ── State label ─────────────────────────────────────────────────────

/**
 * Get the display label (translation key) for a state ID.
 */
export function getSOPStatusLabel(status, config = sopWorkflowConfig) {
    const state = config.states.find((s) => s.id === status)
    return state?.label || status
}

// ── Versioning checks ───────────────────────────────────────────────

/**
 * Check whether a new version can be created from the current state.
 */
export function canCreateNewSOPVersion(status, config = sopWorkflowConfig) {
    return config.versioning.allowNewVersionFrom.includes(status)
}

// ── Audit trail ─────────────────────────────────────────────────────

/**
 * Create a timestamped audit entry. This is generic and does not
 * contain business rules — it simply records what happened.
 */
export function createAuditEntry({
    action,
    fromStatus = null,
    toStatus = null,
    note = '',
    actor = 'System',
    version = null,
}) {
    return {
        id: `audit_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        action,
        fromStatus,
        toStatus,
        note,
        actor,
        version,
        createdAt: new Date().toISOString(),
    }
}

// ── Transition execution ────────────────────────────────────────────

/**
 * Execute a state transition. Checks whether the transition is valid,
 * creates an audit entry, and returns the updated trail.
 *
 * NOTE: This does NOT validate required fields — that is the job
 * of validateSOPTransition() in sopValidation.js.
 * This function only checks that the state→state move is allowed.
 */
export function transitionSOP({
    currentStatus,
    nextStatus,
    note = '',
    actor = 'System',
    version = null,
    currentTrail = [],
    config = sopWorkflowConfig,
}) {
    if (!canTransitionSOP(currentStatus, nextStatus, config)) {
        return {
            ok: false,
            error: `Invalid SOP transition: ${currentStatus} -> ${nextStatus}`,
            nextTrail: currentTrail,
        }
    }

    const entry = createAuditEntry({
        action: nextStatus,
        fromStatus: currentStatus,
        toStatus: nextStatus,
        note,
        actor,
        version,
    })

    return {
        ok: true,
        error: null,
        nextTrail: [...currentTrail, entry],
    }
}