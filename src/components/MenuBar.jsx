/**
 * MenuBar.jsx
 *
 * Renders the top formatting and action toolbar for the editor.
 * Provides buttons for styling text, saving, creating versions,
 * exporting, comparing versions, and inserting tables/placeholders.
 */

import React, { useRef, useState } from 'react'
import { useEditorState } from '@tiptap/react'
import { menuBarStateSelector } from './menuBarState'
import { useLanguage } from '../context/LanguageContext'

// Utility to determine OS for keyboard shortcuts
const isMac =
    typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)

const modKey = isMac ? 'Cmd' : 'Ctrl'
const shortcut = (key) => `${modKey} + ${key}`
const shortcutShift = (key) => `${modKey} + Shift + ${key}`
const shortcutAlt = (key) => `${modKey} + Alt + ${key}`

export const MenuBar = ({
    editor,
    onSave,
    onNewVersion,
    onCreateNewDocument,
    onDuplicateAsNewDocument,
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
    onOCRUpload,
    isOcrLoading,
    ocrError,
    isReadOnly = false,
    canCreateNewVersion = true
}) => {
    const fileInputRef = useRef(null)
    const { t } = useLanguage()
    const [selectedPlaceholder, setSelectedPlaceholder] = useState('')

    const handleOCRButtonClick = () => {
        if (isReadOnly) return
        fileInputRef.current?.click()
    }

    const handleFileChange = async (event) => {
        if (isReadOnly) {
            event.target.value = ''
            return
        }

        const file = event.target.files?.[0]
        if (!file) return

        await onOCRUpload?.(file)
        event.target.value = ''
    }

    const editorState = useEditorState({
        editor,
        selector: menuBarStateSelector,
    })

    if (!editor) return null

    const isInTable = editor.isActive('table')

    const runIfEditable = (callback) => {
        if (isReadOnly) return
        callback?.()
    }

    const disabledIfReadOnly = (extraCondition = false) =>
        isReadOnly || extraCondition

    return (
        <div className="control-group">
            <div className="button-group">
                <button
                    type="button"
                    onClick={() => runIfEditable(onSave)}
                    title={`${t.save} (${shortcut('S')})`}
                    className="save-btn"
                    disabled={isReadOnly}
                >
                    {t.save}
                </button>



                <button
                    type="button"
                    onClick={onNewVersion}
                    title={`${t.newVersion} (${shortcutShift('V')})`}
                    className="version-btn"
                    disabled={!canCreateNewVersion}
                >
                    {t.newVersion}
                </button>

                {/* ── Document Management buttons ───────────────────────── */}
                <span style={{
                    display: 'inline-block',
                    width: 1,
                    height: 22,
                    background: 'rgba(255,255,255,0.15)',
                    margin: '0 6px',
                    verticalAlign: 'middle',
                }} />

                <button
                    type="button"
                    className="save-btn"
                    onClick={onCreateNewDocument}
                    title="Create a brand-new SOP document with a new permanent document ID"
                >
                    New Document
                </button>

                <button
                    type="button"
                    className="save-btn"
                    onClick={onDuplicateAsNewDocument}
                    title="Copy current content into a brand-new document with a new document ID"
                >
                    Duplicate Doc
                </button>

                <span style={{
                    display: 'inline-block',
                    width: 1,
                    height: 22,
                    background: 'rgba(255,255,255,0.15)',
                    margin: '0 6px',
                    verticalAlign: 'middle',
                }} />
                {/* ─────────────────────────────────────────────────────── */}



                <select
                    value={currentVersion}
                    onChange={(e) => onLoadVersion(e.target.value)}
                    className="version-select"
                >
                    {versions.map((v) => (
                        <option key={v.id} value={v.id}>
                            v{v.versionNumber || '?'} ({v.timestamp})
                        </option>
                    ))}
                </select>

                <button
                    type="button"
                    onClick={onOpenPreview}
                    className="pdf-export-btn"
                    title={`${t.previewExport} (${shortcutAlt('P')})`}
                >
                    {t.previewExport}
                </button>

                <button
                    type="button"
                    title={`${t.bold} (${shortcut('B')})`}
                    onClick={() =>
                        runIfEditable(() => editor.chain().focus().toggleBold().run())
                    }
                    disabled={disabledIfReadOnly(!editorState.canBold)}
                    className={editorState.isBold ? 'is-active' : ''}
                >
                    {t.bold}
                </button>

                <button
                    type="button"
                    title={`${t.italic} (${shortcut('I')})`}
                    onClick={() =>
                        runIfEditable(() => editor.chain().focus().toggleItalic().run())
                    }
                    disabled={disabledIfReadOnly(!editorState.canItalic)}
                    className={editorState.isItalic ? 'is-active' : ''}
                >
                    {t.italic}
                </button>

                <button
                    type="button"
                    title={`${t.underline} (${shortcut('U')})`}
                    onClick={() =>
                        runIfEditable(() => editor.chain().focus().toggleUnderline().run())
                    }
                    disabled={disabledIfReadOnly(false)}
                    className={editorState.isUnderline ? 'is-active' : ''}
                >
                    {t.underline}
                </button>

                <button
                    type="button"
                    title={`${t.strike} (${shortcutShift('X')})`}
                    onClick={() =>
                        runIfEditable(() => editor.chain().focus().toggleStrike().run())
                    }
                    disabled={disabledIfReadOnly(!editorState.canStrike)}
                    className={editorState.isStrike ? 'is-active' : ''}
                >
                    {t.strike}
                </button>

                <button
                    type="button"
                    title={`${t.heading1} (Alt + 1)`}
                    onClick={() =>
                        runIfEditable(() =>
                            editor.chain().focus().toggleHeading({ level: 1 }).run()
                        )
                    }
                    disabled={disabledIfReadOnly(false)}
                    className={editorState.isHeading1 ? 'is-active' : ''}
                >
                    {t.heading1}
                </button>

                <button
                    type="button"
                    title={`${t.heading2} (Alt + 2)`}
                    onClick={() =>
                        runIfEditable(() =>
                            editor.chain().focus().toggleHeading({ level: 2 }).run()
                        )
                    }
                    disabled={disabledIfReadOnly(false)}
                    className={editorState.isHeading2 ? 'is-active' : ''}
                >
                    {t.heading2}
                </button>

                <button
                    type="button"
                    title={`${t.heading3} (Alt + 3)`}
                    onClick={() =>
                        runIfEditable(() =>
                            editor.chain().focus().toggleHeading({ level: 3 }).run()
                        )
                    }
                    disabled={disabledIfReadOnly(false)}
                    className={editorState.isHeading3 ? 'is-active' : ''}
                >
                    {t.heading3}
                </button>

                <button
                    type="button"
                    title={`${t.bulletList} (${shortcutShift('L')})`}
                    onClick={() =>
                        runIfEditable(() => editor.chain().focus().toggleBulletList().run())
                    }
                    disabled={disabledIfReadOnly(false)}
                    className={editorState.isBulletList ? 'is-active' : ''}
                >
                    {t.bulletList}
                </button>

                <button
                    type="button"
                    title={`${t.numberedList} (${shortcutShift('7')})`}
                    onClick={() =>
                        runIfEditable(() =>
                            editor.chain().focus().toggleOrderedList().run()
                        )
                    }
                    disabled={disabledIfReadOnly(false)}
                    className={editorState.isOrderedList ? 'is-active' : ''}
                >
                    {t.numberedList}
                </button>

                <button
                    type="button"
                    title={`${t.undo} (${shortcut('Z')})`}
                    onClick={() =>
                        runIfEditable(() => editor.chain().focus().undo().run())
                    }
                    disabled={disabledIfReadOnly(!editorState.canUndo)}
                >
                    {t.undo}
                </button>

                <button
                    type="button"
                    title={`${t.redo} (${shortcutShift('Z')})`}
                    onClick={() =>
                        runIfEditable(() => editor.chain().focus().redo().run())
                    }
                    disabled={disabledIfReadOnly(!editorState.canRedo)}
                >
                    {t.redo}
                </button>

                <button
                    type="button"
                    title={`${t.insertUrl} (${shortcut('K')})`}
                    onClick={() => runIfEditable(onOpenLinkModal)}
                    disabled={isReadOnly}
                >
                    {t.insertUrl}
                </button>

                {profile?.toLowerCase() === 'contract' && (
                    <select
                        className="version-select"
                        value={selectedPlaceholder}
                        disabled={isReadOnly}
                        onChange={(e) => {
                            if (isReadOnly) return

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
                        {versions.map((v) => (
                            <option key={v.id} value={v.id}>
                                {t.base}: v{v.versionNumber || '?'}
                            </option>
                        ))}
                    </select>

                    <span className="compare-vs">{t.vs}</span>

                    <select
                        id="compareV2"
                        className="version-select"
                        defaultValue={versions[versions.length - 1]?.id}
                    >
                        {versions.map((v) => (
                            <option key={v.id} value={v.id}>
                                {t.target}: v{v.versionNumber || '?'}
                            </option>
                        ))}
                    </select>

                    <button
                        type="button"
                        className="compare-btn"
                        title={t.compare}
                        onClick={() => {
                            const v1 = document.getElementById('compareV1').value
                            const v2 = document.getElementById('compareV2').value
                            onCompare(v1, v2)
                        }}
                    >
                        {t.compare}
                    </button>
                </div>

                <button
                    type="button"
                    title={t.insertTable}
                    onClick={() =>
                        runIfEditable(() =>
                            editor
                                .chain()
                                .focus()
                                .insertTable({ rows: 4, cols: 4, withHeaderRow: true })
                                .run()
                        )
                    }
                    disabled={isReadOnly}
                >
                    {t.insertTable}
                </button>

                <button
                    type="button"
                    onClick={handleOCRButtonClick}
                    disabled={isReadOnly || isOcrLoading}
                    title={t.importOcrTooltip}
                >
                    {isOcrLoading ? t.extracting : t.importPdfDocx}
                </button>

                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.doc,.txt"
                    style={{ display: 'none' }}
                    onChange={handleFileChange}
                />

                {isInTable && (
                    <>
                        <button
                            type="button"
                            title={t.addColBefore}
                            onClick={() =>
                                runIfEditable(() =>
                                    editor.chain().focus().addColumnBefore().run()
                                )
                            }
                            disabled={isReadOnly}
                        >
                            {t.addColBefore}
                        </button>

                        <button
                            type="button"
                            title={t.addColAfter}
                            onClick={() =>
                                runIfEditable(() =>
                                    editor.chain().focus().addColumnAfter().run()
                                )
                            }
                            disabled={isReadOnly}
                        >
                            {t.addColAfter}
                        </button>

                        <button
                            type="button"
                            title={t.deleteColumn}
                            onClick={() =>
                                runIfEditable(() =>
                                    editor.chain().focus().deleteColumn().run()
                                )
                            }
                            disabled={isReadOnly}
                        >
                            {t.deleteColumn}
                        </button>

                        <button
                            type="button"
                            title={t.addRowBefore}
                            onClick={() =>
                                runIfEditable(() => editor.chain().focus().addRowBefore().run())
                            }
                            disabled={isReadOnly}
                        >
                            {t.addRowBefore}
                        </button>

                        <button
                            type="button"
                            title={t.addRowAfter}
                            onClick={() =>
                                runIfEditable(() => editor.chain().focus().addRowAfter().run())
                            }
                            disabled={isReadOnly}
                        >
                            {t.addRowAfter}
                        </button>

                        <button
                            type="button"
                            title={t.deleteRow}
                            onClick={() =>
                                runIfEditable(() => editor.chain().focus().deleteRow().run())
                            }
                            disabled={isReadOnly}
                        >
                            {t.deleteRow}
                        </button>

                        <button
                            type="button"
                            title={t.deleteTable}
                            onClick={() =>
                                runIfEditable(() => editor.chain().focus().deleteTable().run())
                            }
                            disabled={isReadOnly}
                        >
                            {t.deleteTable}
                        </button>
                    </>
                )}
            </div>
        </div>
    )
}

export default MenuBar