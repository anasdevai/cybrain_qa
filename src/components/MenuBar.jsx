import { useEditorState } from "@tiptap/react";
import { menuBarStateSelector } from "./menuBarState";
import { useState } from "react";


const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform)

const modKey = isMac ? "Cmd" : "Ctrl"

const shortcut = (key) => `${modKey} + ${key}`
const shortcutShift = (key) => `${modKey} + Shift + ${key}`
const shortcutAlt = (key) => `${modKey} + Alt + ${key}`

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
    const editorState = useEditorState({
        editor,
        selector: menuBarStateSelector,
    });


    const [selectedPlaceholder, setSelectedPlaceholder] = useState("");





    if (!editor) return null;

    const isInTable = editor.isActive("table");

    return (
        <div className="control-group">
            <div className="button-group">

                <button
                    type="button"
                    onClick={onSave}
                    title={`Manual Save (${shortcut("S")})`}
                    className="save-btn"
                >
                    Save
                </button>

                <button
                    type="button"
                    onClick={onNewVersion}
                    title={`Create New Version (${shortcutShift("V")})`}
                    className="version-btn"
                >
                    New Version
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
                    title={`Preview / Export PDF (${shortcutAlt("P")})`}
                >
                    Preview & Export
                </button>

                <button
                    type="button"
                    title={`Bold (${shortcut("B")})`}
                    onClick={() => editor.chain().focus().toggleBold().run()}
                    disabled={!editorState.canBold}
                    className={editorState.isBold ? "is-active" : ""}
                >
                    Bold
                </button>

                <button
                    type="button"
                    title={`Italic (${shortcut("I")})`}
                    onClick={() => editor.chain().focus().toggleItalic().run()}
                    disabled={!editorState.canItalic}
                    className={editorState.isItalic ? "is-active" : ""}
                >
                    Italic
                </button>



                <button
                    type="button"
                    title={`Underline (${shortcut("U")})`}
                    onClick={() => editor.chain().focus().toggleUnderline().run()}
                    className={editorState.isUnderline ? "is-active" : ""}
                >
                    Underline
                </button>



                <button
                    type="button"
                    title={`Strikethrough (${shortcutShift("X")})`}
                    onClick={() => editor.chain().focus().toggleStrike().run()}
                    disabled={!editorState.canStrike}
                    className={editorState.isStrike ? "is-active" : ""}
                >
                    Strike
                </button>

                <button
                    type="button"
                    title={`Heading 1 (${isMac ? "Alt + 1" : "Alt + 1"})`}
                    onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                    className={editorState.isHeading1 ? "is-active" : ""}
                >
                    Heading 1
                </button>

                <button
                    type="button"
                    title={`Heading 2 (${isMac ? "Alt + 2" : "Alt + 2"})`}
                    onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                    className={editorState.isHeading2 ? "is-active" : ""}
                >
                    Heading 2
                </button>

                <button
                    type="button"
                    title={`Heading 3 (${isMac ? "Alt + 3" : "Alt + 3"})`}
                    onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
                    className={editorState.isHeading3 ? "is-active" : ""}
                >
                    Heading 3
                </button>

                <button
                    type="button"
                    title={`Bullet List (${shortcutShift("L")})`}
                    onClick={() => editor.chain().focus().toggleBulletList().run()}
                    className={editorState.isBulletList ? "is-active" : ""}
                >
                    Bullet List
                </button>

                <button
                    type="button"
                    title={`Numbered List (${shortcutShift("7")})`}
                    onClick={() => editor.chain().focus().toggleOrderedList().run()}
                    className={editorState.isOrderedList ? "is-active" : ""}
                >
                    Numbered List
                </button>

                <button
                    type="button"
                    title={`Undo (${shortcut("Z")})`}
                    onClick={() => editor.chain().focus().undo().run()}
                    disabled={!editorState.canUndo}
                >
                    Undo
                </button>

                <button
                    type="button"
                    title={`Redo (${shortcutShift("Z")})`}
                    onClick={() => editor.chain().focus().redo().run()}
                    disabled={!editorState.canRedo}
                >
                    Redo
                </button>

                <button
                    type="button"
                    title={`Insert Link (${shortcut("K")})`}
                    onClick={onOpenLinkModal}
                >
                    Insert URL
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
                                const customName = window.prompt('Enter custom placeholder name')
                                if (customName?.trim()) {
                                    onInsertPlaceholder?.(customName.trim())
                                    setSelectedPlaceholder(customName.trim())
                                }
                            } else {
                                onInsertPlaceholder?.(value)
                            }
                        }}
                    >
                        <option value="">Insert Placeholder</option>
                        <option value="ClientName">Client Name</option>
                        <option value="Address">Address</option>
                        <option value="Date">Date</option>
                        <option value="Amount">Amount</option>
                        <option value="__custom__">Custom...</option>
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
                                Base: {v.id}
                            </option>
                        ))}
                    </select>

                    <span className="compare-vs">vs</span>

                    <select
                        id="compareV2"
                        className="version-select"
                        defaultValue={versions[versions.length - 1]?.id}
                    >
                        {versions.map(v => (
                            <option key={v.id} value={v.id}>
                                Target: {v.id}
                            </option>
                        ))}
                    </select>

                    <button
                        type="button"
                        className="compare-btn"
                        title="Compare Versions"
                        onClick={() => {
                            const v1 = document.getElementById("compareV1").value;
                            const v2 = document.getElementById("compareV2").value;
                            onCompare(v1, v2);
                        }}
                    >
                        Compare
                    </button>
                </div>

                <button
                    type="button"
                    title={`Insert Table (Alt + T)`}
                    onClick={() => editor.chain().focus().insertTable({ rows: 4, cols: 4, withHeaderRow: true }).run()}
                >
                    Insert Table
                </button>

                {isInTable && (
                    <>
                        <button
                            type="button"
                            title="Add Column Before"
                            onClick={() => editor.chain().focus().addColumnBefore().run()}
                        >
                            Add Col Before
                        </button>

                        <button
                            type="button"
                            title="Add Column After"
                            onClick={() => editor.chain().focus().addColumnAfter().run()}
                        >
                            Add Col After
                        </button>

                        <button
                            type="button"
                            title="Delete Column"
                            onClick={() => editor.chain().focus().deleteColumn().run()}
                        >
                            Delete Column
                        </button>

                        <button
                            type="button"
                            title="Add Row Before"
                            onClick={() => editor.chain().focus().addRowBefore().run()}
                        >
                            Add Row Before
                        </button>

                        <button
                            type="button"
                            title="Add Row After"
                            onClick={() => editor.chain().focus().addRowAfter().run()}
                        >
                            Add Row After
                        </button>

                        <button
                            type="button"
                            title="Delete Row"
                            onClick={() => editor.chain().focus().deleteRow().run()}
                        >
                            Delete Row
                        </button>

                        <button
                            type="button"
                            title="Delete Table"
                            onClick={() => editor.chain().focus().deleteTable().run()}
                        >
                            Delete Table
                        </button>
                    </>
                )}
            </div>
        </div>
    );
};

export default MenuBar;