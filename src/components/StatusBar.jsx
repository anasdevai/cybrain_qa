import React from 'react'
import { useLanguage } from '../context/LanguageContext'
import featureFlags from '../config/featureFlags'

/**
 * StatusBar Component
 *
 * Displays live document statistics, profile/language selectors,
 * and the current save state at the bottom of the editor.
 */
const StatusBar = ({
    wordCount,
    charCount = 0,
    blockCount = 0,
    lastSaved,
    isSaving,
    profile = 'contract',
    onProfileChange,
    workflowStatus = '',
}) => {
    const { language, setLanguage, t } = useLanguage()

    const statusLabelMap = {
        draft: t.draft,
        under_review: t.underReview,
        changes_requested: t.changesRequested,
        accepted: t.accepted,
        rejected: t.rejected,
        effective: t.effective || 'Effective',
        obsolete: t.obsolete || 'Obsolete',

        Draft: t.draft,
        'Under Review': t.underReview,
        'Changes Requested': t.changesRequested,
        Accepted: t.accepted,
        Rejected: t.rejected,
        Effective: t.effective || 'Effective',
        Obsolete: t.obsolete || 'Obsolete',
    }

    const displayWorkflowStatus =
        statusLabelMap[workflowStatus] || workflowStatus || ''

    return (
        <div className="status-bar">
            <div className="status-left">
                <span className="word-count">
                    {wordCount} {t.words} | {charCount} {t.characters} | {blockCount} {t.blocks}
                </span>
            </div>

            <div className="status-center">
                <select
                    value={profile}
                    onChange={(e) => onProfileChange(e.target.value)}
                    className="version-select profile-select-status"
                >
                    {featureFlags.contractProfileEnabled && (
                        <option value="contract">{t.profileContract}</option>
                    )}
                    {featureFlags.sopProfileEnabled && (
                        <option value="sop">{t.profileSop}</option>
                    )}
                </select>

                <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="version-select profile-select-status"
                >
                    <option value="en">{t.english}</option>
                    <option value="de">{t.german}</option>
                </select>
            </div>

            <div className="status-right">
                {displayWorkflowStatus ? (
                    <span className="workflow-status-chip">
                        {displayWorkflowStatus}
                    </span>
                ) : null}

                {isSaving ? (
                    <span className="saving-indicator">{t.saving}</span>
                ) : (
                    <span className="last-saved">
                        {t.saved} {lastSaved ? lastSaved.toLocaleTimeString() : t.never}
                    </span>
                )}
            </div>
        </div>
    )
}

export default StatusBar