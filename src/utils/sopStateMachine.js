import {
    SOP_ACTIONS,
    SOP_LABELS,
    SOP_STATES,
} from './sopConstants'

export const SOP_TRANSITIONS = {
    [SOP_STATES.DRAFT]: [SOP_STATES.UNDER_REVIEW],
    [SOP_STATES.UNDER_REVIEW]: [SOP_STATES.DRAFT, SOP_STATES.EFFECTIVE],
    [SOP_STATES.EFFECTIVE]: [SOP_STATES.OBSOLETE],
    [SOP_STATES.OBSOLETE]: [],
}

export const canTransitionSOP = (from, to) => {
    return SOP_TRANSITIONS[from]?.includes(to) || false
}

export const canEditSOP = (status) => status === SOP_STATES.DRAFT

export const getAllowedSOPActions = (status) => {
    switch (status) {
        case SOP_STATES.DRAFT:
            return [SOP_ACTIONS.SUBMIT_REVIEW]
        case SOP_STATES.UNDER_REVIEW:
            return [SOP_ACTIONS.APPROVE, SOP_ACTIONS.SEND_BACK]
        case SOP_STATES.EFFECTIVE:
            return [SOP_ACTIONS.MARK_OBSOLETE]
        case SOP_STATES.OBSOLETE:
        default:
            return []
    }
}

export const getSOPStatusLabel = (status) => {
    return SOP_LABELS[status] || status
}

export const createAuditEntry = ({
    action,
    fromStatus = null,
    toStatus = null,
    note = '',
    actor = 'System',
}) => ({
    id: `audit_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    action,
    fromStatus,
    toStatus,
    note,
    actor,
    createdAt: new Date().toISOString(),
})

export const transitionSOP = ({
    currentStatus,
    nextStatus,
    note = '',
    actor = 'System',
    currentTrail = [],
}) => {
    if (!canTransitionSOP(currentStatus, nextStatus)) {
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
    })

    return {
        ok: true,
        error: null,
        nextTrail: [...currentTrail, entry],
    }
}