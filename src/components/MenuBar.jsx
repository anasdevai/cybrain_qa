/**
 * MenuBar.jsx
 * 
 * Renders the top formatting and action toolbar for the editor.
 * Provides buttons for styling text, saving, creating versions,
 * exporting, comparing versions, and inserting tables/placeholders.
 */

import { useEditorState } from "@tiptap/react";
import { menuBarStateSelector } from "./menuBarState";
import { useState } from "react";
import { useLanguage } from "../context/LanguageContext";

// Utility to determine OS for keyboard shortcuts
const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform)
const modKey = isMac ? "Cmd" : "Ctrl"
const shortcut = (key) => `${modKey} + ${key}`
const shortcutShift = (key) => `${modKey} + Shift + ${key}`
const shortcutAlt = (key) => `${modKey} + Alt + ${key}`

/**
 * MenuBar Component
 * 
 * @param {Object} props
 * @param {Object} props.editor - The Tiptap editor instance.
 * @param {Function} props.onSave - Callback to trigger manual save.
 * @param {Function} props.onNewVersion - Callback to create a new version.
 * @param {string} props.currentVersion - The ID of the currently active version.
 * @param {Function} props.onLoadVersion - Callback when a version is selected from the dropdown.
 * @param {Array} props.versions - List of all document versions.
 * @param {Function} props.onOpenLinkModal - Callback to open the insert link modal.
 * @param {Function} props.onCompare - Callback to compare two selected versions.
 * @param {Function} props.onOpenPreview - Callback to open the PDF/preview modal.
 * @param {Function} props.onInsertPlaceholder - Callback when a placeholder variable is selected.
 * @param {string} props.profile - The active user profile ('contract', 'simple').
 * @param {Function} props.onToggleVariablesPanel - Callback to toggle the variables sidebar.
 * @param {Function} props.onSendForReview - Callback to start the review workflow.
 */
export const MenuBar = ({
    editor,
    onSave,
    onNewVersion,
    currentVersion,
    onLoadVersion,
    versions,
    onOpenLinkModal,
    onCompare,
    onOpenPreview,
    onInsertPlaceholder,
    profile,
    onToggleVariablesPanel,
    onSendForReview,
}) => {
    // Subscribes to editor state changes (e.g., is text bold?) efficiently
    const editorState = useEditorState({
        editor,
        selector: menuBarStateSelector,
    });

    const { t } = useLanguage();
    const [selectedPlaceholder, setSelectedPlaceholder] = useState("");

    if (!editor) return null;

    // Checks if cursor/selection is currently inside a table
    const isInTable = editor.isActive("table");

    return (
        <div className="control-group">
            <div className="button-group">

                <button
                    type="button"
                    onClick={onSave}
                    title={`${t.save} (${shortcut("S")})`}
                    className="save-btn"
                >
                    {t.save}
                </button>

                <button
                    type="button"
                    onClick={onNewVersion}
                    title={`${t.newVersion} (${shortcutShift("V")})`}
                    className="version-btn"
                >
                    {t.newVersion}
                </button>

                <select
                    value={currentVersion}
                    onChange={(e) => onLoadVersion(e.target.value)}
                    className="version-select"
                >
                    {versions.map(v => (
                        <option key={v.id} value={v.id}>
                            {v.id} ({v.timestamp})
                        </option>
                    ))}
                </select>

                <button
                    type="button"
                    onClick={onOpenPreview}
                    className="pdf-export-btn"
                    title={`${t.previewExport} (${shortcutAlt("P")})`}
                >
                    {t.previewExport}
                </button>

                <button
                    type="button"
                    title={`${t.bold} (${shortcut("B")})`}
                    onClick={() => editor.chain().focus().toggleBold().run()}
                    disabled={!editorState.canBold}
                    className={editorState.isBold ? "is-active" : ""}
                >
                    {t.bold}
                </button>

                <button
                    type="button"
                    title={`${t.italic} (${shortcut("I")})`}
                    onClick={() => editor.chain().focus().toggleItalic().run()}
                    disabled={!editorState.canItalic}
                    className={editorState.isItalic ? "is-active" : ""}
                >
                    {t.italic}
                </button>

                <button
                    type="button"
                    title={`${t.underline} (${shortcut("U")})`}
                    onClick={() => editor.chain().focus().toggleUnderline().run()}
                    className={editorState.isUnderline ? "is-active" : ""}
                >
                    {t.underline}
                </button>

                <button
                    type="button"
                    title={`${t.strike} (${shortcutShift("X")})`}
                    onClick={() => editor.chain().focus().toggleStrike().run()}
                    disabled={!editorState.canStrike}
                    className={editorState.isStrike ? "is-active" : ""}
                >
                    {t.strike}
                </button>

                <button
                    type="button"
                    title={`${t.heading1} (Alt + 1)`}
                    onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                    className={editorState.isHeading1 ? "is-active" : ""}
                >
                    {t.heading1}
                </button>

                <button
                    type="button"
                    title={`${t.heading2} (Alt + 2)`}
                    onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                    className={editorState.isHeading2 ? "is-active" : ""}
                >
                    {t.heading2}
                </button>

                <button
                    type="button"
                    title={`${t.heading3} (Alt + 3)`}
                    onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
                    className={editorState.isHeading3 ? "is-active" : ""}
                >
                    {t.heading3}
                </button>

                <button
                    type="button"
                    title={`${t.bulletList} (${shortcutShift("L")})`}
                    onClick={() => editor.chain().focus().toggleBulletList().run()}
                    className={editorState.isBulletList ? "is-active" : ""}
                >
                    {t.bulletList}
                </button>

                <button
                    type="button"
                    title={`${t.numberedList} (${shortcutShift("7")})`}
                    onClick={() => editor.chain().focus().toggleOrderedList().run()}
                    className={editorState.isOrderedList ? "is-active" : ""}
                >
                    {t.numberedList}
                </button>

                <button
                    type="button"
                    title={`${t.undo} (${shortcut("Z")})`}
                    onClick={() => editor.chain().focus().undo().run()}
                    disabled={!editorState.canUndo}
                >
                    {t.undo}
                </button>

                <button
                    type="button"
                    title={`${t.redo} (${shortcutShift("Z")})`}
                    onClick={() => editor.chain().focus().redo().run()}
                    disabled={!editorState.canRedo}
                >
                    {t.redo}
                </button>

                <button
                    type="button"
                    title={`${t.insertUrl} (${shortcut("K")})`}
                    onClick={onOpenLinkModal}
                >
                    {t.insertUrl}
                </button>

                {profile?.toLowerCase() === 'contract' && (
                    <select
                        className="version-select"
                        value={selectedPlaceholder}
                        onChange={(e) => {
                            const value = e.target.value
                            setSelectedPlaceholder(value)

                            if (!value) return

                            if (value === '__custom__') {
                                const customName = window.prompt(t.custom)
                                if (customName?.trim()) {
                                    onInsertPlaceholder?.(customName.trim())
                                    setSelectedPlaceholder(customName.trim())
                                }
                            } else {
                                onInsertPlaceholder?.(value)
                            }
                        }}
                    >
                        <option value="">{t.insertPlaceholder}</option>
                        <option value="ClientName">{t.clientName}</option>
                        <option value="Address">{t.address}</option>
                        <option value="Date">{t.date}</option>
                        <option value="Amount">{t.amount}</option>
                        <option value="__custom__">{t.custom}</option>
                    </select>
                )}

                <div className="compare-controls">
                    <select
                        id="compareV1"
                        className="version-select"
                        defaultValue={versions[versions.length - 2]?.id}
                    >
                        {versions.map(v => (
                            <option key={v.id} value={v.id}>
                                {t.base}: {v.id}
                            </option>
                        ))}
                    </select>

                    <span className="compare-vs">{t.vs}</span>

                    <select
                        id="compareV2"
                        className="version-select"
                        defaultValue={versions[versions.length - 1]?.id}
                    >
                        {versions.map(v => (
                            <option key={v.id} value={v.id}>
                                {t.target}: {v.id}
                            </option>
                        ))}
                    </select>

                    <button
                        type="button"
                        className="compare-btn"
                        title={t.compare}
                        onClick={() => {
                            const v1 = document.getElementById("compareV1").value;
                            const v2 = document.getElementById("compareV2").value;
                            onCompare(v1, v2);
                        }}
                    >
                        {t.compare}
                    </button>
                </div>

                <button
                    type="button"
                    title={t.insertTable}
                    onClick={() => editor.chain().focus().insertTable({ rows: 4, cols: 4, withHeaderRow: true }).run()}
                >
                    {t.insertTable}
                </button>

                {isInTable && (
                    <>
                        <button
                            type="button"
                            title={t.addColBefore}
                            onClick={() => editor.chain().focus().addColumnBefore().run()}
                        >
                            {t.addColBefore}
                        </button>

                        <button
                            type="button"
                            title={t.addColAfter}
                            onClick={() => editor.chain().focus().addColumnAfter().run()}
                        >
                            {t.addColAfter}
                        </button>

                        <button
                            type="button"
                            title={t.deleteColumn}
                            onClick={() => editor.chain().focus().deleteColumn().run()}
                        >
                            {t.deleteColumn}
                        </button>

                        <button
                            type="button"
                            title={t.addRowBefore}
                            onClick={() => editor.chain().focus().addRowBefore().run()}
                        >
                            {t.addRowBefore}
                        </button>

                        <button
                            type="button"
                            title={t.addRowAfter}
                            onClick={() => editor.chain().focus().addRowAfter().run()}
                        >
                            {t.addRowAfter}
                        </button>

                        <button
                            type="button"
                            title={t.deleteRow}
                            onClick={() => editor.chain().focus().deleteRow().run()}
                        >
                            {t.deleteRow}
                        </button>

                        <button
                            type="button"
                            title={t.deleteTable}
                            onClick={() => editor.chain().focus().deleteTable().run()}
                        >
                            {t.deleteTable}
                        </button>
                    </>
                )}
            </div>
        </div>
    );
};

export default MenuBar;