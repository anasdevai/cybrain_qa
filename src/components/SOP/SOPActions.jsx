/**
 * SOPActions.jsx
 *
 * Config-driven SOP workflow action panel.
 * Also renders the Document Management section for:
 *   - Create New Version  (same sops.id, new sop_versions row)
 *   - Create New Document (new sops.id, new v1)
 *   - Duplicate as New Document (fork content into a new sops.id)
 */
import { useMemo, useState } from 'react'
import { useLanguage } from '../../context/LanguageContext'
import { useSOPConfig } from '../../context/SOPConfigContext'
import { getAllowedTransitions } from '../../utils/sopStateMachine'

export default function SOPActions({
    sopStatus,
    onAction,
    isClientReviewMode = false,
    // ── Document management handlers (passed from App.jsx) ──
    onCreateNewVersion,
    onCreateNewDocument,
    onDuplicateAsNewDocument,
    canCreateNewVersion = false,
}) {
    const { t } = useLanguage()
    const config = useSOPConfig()

    const [note, setNote] = useState('')
    const [actionFields, setActionFields] = useState({})
    const [error, setError] = useState('')

    // Get allowed [actionId, transitionConfig] pairs for current status
    const allowedTransitions = useMemo(
        () => getAllowedTransitions(sopStatus, config),
        [sopStatus, config]
    )

    // Resolve display label for current status
    const statusState = config.states.find((s) => s.id === sopStatus)
    const displayStatus = statusState ? (t[statusState.label] || statusState.label) : sopStatus

    // Collect all unique extra fields across allowed transitions
    const visibleFields = useMemo(() => {
        const fieldMap = new Map()
        for (const [, transition] of allowedTransitions) {
            for (const field of transition.fields || []) {
                if (!fieldMap.has(field.key)) {
                    fieldMap.set(field.key, field)
                }
            }
        }
        return Array.from(fieldMap.values())
    }, [allowedTransitions])

    // Update a single action field value
    const updateField = (key, value) => {
        setActionFields((prev) => ({ ...prev, [key]: value }))
    }

    // Execute a transition action
    const runAction = async (actionId) => {
        const result = await onAction?.(actionId, {
            note: note.trim(),
            actionFields,
        })

        if (result?.ok === false) {
            setError(result.error || t.noteRequired || 'This action requires more information.')
            return
        }

        // Reset all inputs on success
        setError('')
        setNote('')
        setActionFields({})
    }

    // Read-only mode — no actions available
    if (isClientReviewMode) {
        return (
            <div className="review-actions">
                <h3>{t.sopActions}</h3>
                <p className="muted-text">{t.readOnlyModeEnabled}</p>
            </div>
        )
    }

    return (
        <div className="review-actions">
            <h3>{t.sopActions}</h3>

            <p>
                <strong>{t.currentStatus}:</strong> {displayStatus}
            </p>

            {/* Note textarea — always shown when actions are available */}
            {allowedTransitions.length > 0 && (
                <textarea
                    value={note}
                    onChange={(e) => {
                        setNote(e.target.value)
                        if (error) setError('')
                    }}
                    rows={4}
                    placeholder={t.sopNotePlaceholder}
                    className="review-comment-box"
                />
            )}

            {/* Dynamic extra fields — rendered from config */}
            {visibleFields.map((field) => (
                <input
                    key={field.key}
                    type={field.type || 'text'}
                    value={actionFields[field.key] || ''}
                    onChange={(e) => updateField(field.key, e.target.value)}
                    placeholder={t[field.label] || field.label}
                />
            ))}

            {/* Error message */}
            {error && (
                <p style={{ color: 'red', fontSize: '13px', marginTop: '6px' }}>
                    {error}
                </p>
            )}

            {/* Dynamic action buttons — rendered from config  */}
            {allowedTransitions.length > 0 && (
                <div
                    className="review-actions-buttons"
                    style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}
                >
                    {allowedTransitions.map(([actionId, transition]) => (
                        <button
                            key={actionId}
                            type="button"
                            className={transition.style || 'primary-btn'}
                            onClick={() => runAction(actionId)}
                        >
                            {t[transition.label] || transition.label}
                        </button>
                    ))}
                </div>
            )}

        </div>
    )
}