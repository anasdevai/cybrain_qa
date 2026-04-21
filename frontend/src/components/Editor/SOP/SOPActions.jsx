import { useMemo, useState } from 'react'
import { Zap, Link, Eye, EyeOff, Activity } from 'lucide-react'
import { useLanguage } from '../../../context/LanguageContext'
import { useSOPConfig } from '../../../context/SOPConfigContext'
import { getAllowedTransitions } from '../../../utils/sopStateMachine'

export default function SOPActions({
    sopStatus,
    onAction,
    isClientReviewMode = false,
    // ── Document management handlers (passed from App.jsx) ──
    onCreateNewVersion,
    onCreateNewDocument,
    onDuplicateAsNewDocument,
    canCreateNewVersion = false,
    onToggleRelated,
    showRelatedContext = true,
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

    // Read-only mode
    if (isClientReviewMode) {
        return (
            <div className="sop-panel-card">
                <h3 className="sop-panel-title">
                  <Zap size={18} />
                  {t.sopActions}
                </h3>
                <p className="muted-text">{t.readOnlyModeEnabled}</p>
            </div>
        )
    }

    return (
        <div className="sop-panel-card">
            <h3 className="sop-panel-title">
                <Zap size={18} />
                {t.sopActions}
            </h3>

            <div className="sop-status-row">
                <span className="sop-status-label">{t.currentStatus}</span>
                <span className="sop-status-value">
                  <Activity size={14} />
                  {displayStatus}
                </span>
            </div>

            {/* Note textarea — always shown when actions are available */}
            {allowedTransitions.length > 0 && (
                <div className="sop-field-group">
                  <label className="sop-field-label">{t.sopNotePlaceholder}</label>
                  <textarea
                    value={note}
                    onChange={(e) => {
                        setNote(e.target.value)
                        if (error) setError('')
                    }}
                    rows={4}
                    className="sop-textarea"
                  />
                </div>
            )}

            {/* Dynamic extra fields — rendered from config */}
            <div className="sop-metadata-grid">
                {visibleFields.map((field) => (
                    <div key={field.key} className="sop-field-group">
                      <label className="sop-field-label">{t[field.label] || field.label}</label>
                      <input
                          type={field.type || 'text'}
                          className="sop-input"
                          value={actionFields[field.key] || ''}
                          onChange={(e) => updateField(field.key, e.target.value)}
                      />
                    </div>
                ))}
            </div>

            {/* Error message */}
            {error && (
                <p className="error-text">
                    {error}
                </p>
            )}

            {/* Dynamic action buttons — rendered from config  */}
            {allowedTransitions.length > 0 && (
                <div className="sop-actions-grid">
                    {allowedTransitions.map(([actionId, transition]) => (
                        <button
                            key={actionId}
                            type="button"
                            className={`sop-action-btn ${transition.style === 'primary' ? 'primary' : 'secondary'}`}
                            onClick={() => runAction(actionId)}
                        >
                            {t[transition.label] || transition.label}
                        </button>
                    ))}
                </div>
            )}

            {/* System Context Buttons */}
            <div className="sop-system-actions">
                 <button 
                   onClick={onToggleRelated}
                   className={`sop-toggle-btn ${showRelatedContext ? 'active' : ''}`}
                 >
                   {showRelatedContext ? <EyeOff size={16} /> : <Eye size={16} />}
                   {showRelatedContext ? 'Verknüpfungen ausblenden' : 'Verknüpfungen anzeigen'}
                 </button>
            </div>
        </div>
    )
}

