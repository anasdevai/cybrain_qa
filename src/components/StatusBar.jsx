import React from 'react';
import { useLanguage } from '../context/LanguageContext';

/**
 * StatusBar Component
 * 
 * Displays live document statistics (word count, char count, block count),
 * global configuration selectors (active profile, language toggles),
 * and the save state indicator at the bottom of the editor.
 * 
 * @param {Object} props
 * @param {number} props.wordCount - Number of words in the active document.
 * @param {number} props.charCount - Number of characters in the active document.
 * @param {number} props.blockCount - Number of top-level blocks in the document.
 * @param {Date|null} props.lastSaved - Timestamp of the most recent save.
 * @param {boolean} props.isSaving - Whether a save operation is currently in progress.
 * @param {string} props.profile - The selected editing profile (e.g., "contract" or "sop").
 * @param {Function} props.onProfileChange - Callback triggered when profile selection changes.
 */
const StatusBar = ({
    wordCount,
    charCount = 0,
    blockCount = 0,
    lastSaved,
    isSaving,
    profile = "contract",
    onProfileChange,
}) => {
    // Utilize globalization context to translate UI strings
    const { language, setLanguage, t } = useLanguage();

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
                    <option value="contract">{t.profileContract}</option>
                    <option value="sop">{t.profileSop}</option>
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
                {isSaving ? (
                    <span className="saving-indicator">{t.saving}</span>
                ) : (
                    <span className="last-saved">
                        {t.saved} {lastSaved ? lastSaved.toLocaleTimeString() : t.never}
                    </span>
                )}
            </div>
        </div>
    );
};

export default StatusBar;