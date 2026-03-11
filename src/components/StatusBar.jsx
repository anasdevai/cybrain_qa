import React from 'react';

const StatusBar = ({
    wordCount,
    charCount = 0,
    blockCount = 0,
    lastSaved,
    isSaving,
    profile = "contract",
    onProfileChange,
}) => {
    return (
        <div className="status-bar">
            <div className="status-left">
                <span className="word-count">
                    {wordCount} words | {charCount} characters | {blockCount} blocks
                </span>
            </div>

            <div className="status-center">
                <select
                    value={profile}
                    onChange={(e) => onProfileChange(e.target.value)}
                    className="version-select profile-select-status"
                >
                    <option value="contract">Profile: Contract</option>
                    <option value="sop">Profile: SOP</option>
                </select>
            </div>

            <div className="status-right">
                {isSaving ? (
                    <span className="saving-indicator">Saving...</span>
                ) : (
                    <span className="last-saved">
                        Saved {lastSaved ? lastSaved.toLocaleTimeString() : 'never'}
                    </span>
                )}
            </div>
        </div>
    );
};

export default StatusBar;