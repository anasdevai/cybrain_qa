/**
 * LinkModal.jsx
 * 
 * A reusable modal dialog component for inserting or editing hyperlinks
 * within the Tiptap editor. Handles focus management and basic URL validation.
 */
import React, { useState, useEffect, useRef } from 'react';

/**
 * Link insertion modal component.
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether the modal is currently displayed.
 * @param {Function} props.onClose - Triggered to dismiss the modal without saving.
 * @param {Function} props.onSave - Triggered to apply the URL to the editor selection.
 * @param {string} props.initialUrl - Pre-populated URL (e.g., if editing an existing link).
 */
const LinkModal = ({ isOpen, onClose, onSave, initialUrl = '' }) => {
    const [url, setUrl] = useState(initialUrl);
    const inputRef = useRef(null);

    // Auto-focus the input cleanly whenever the modal is shown
    useEffect(() => {
        if (isOpen) {
            setUrl(initialUrl);
            setTimeout(() => {
                if (inputRef.current) {
                    inputRef.current.focus();
                }
            }, 10);
        }
    }, [isOpen, initialUrl]);

    if (!isOpen) return null;

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave(url);
    };

    return (
        <div className="link-modal-overlay" onClick={onClose}>
            <div className="link-modal" onClick={(e) => e.stopPropagation()}>
                <div className="link-modal-header">
                    <h3>Insert Link</h3>
                    <button type="button" className="close-btn" onClick={onClose}>&times;</button>
                </div>
                <form onSubmit={handleSubmit} className="link-modal-body">
                    <div className="form-group">
                        <label htmlFor="url-input">Address:</label>
                        <input
                            id="url-input"
                            ref={inputRef}
                            type="url"
                            placeholder="https://example.com"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            required
                        />
                    </div>
                    <div className="link-modal-footer">
                        <button type="button" className="cancel-btn" onClick={onClose}>Cancel</button>
                        <button type="submit" className="ok-btn">OK</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default LinkModal;
