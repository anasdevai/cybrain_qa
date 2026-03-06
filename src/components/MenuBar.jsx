import { useEditorState } from "@tiptap/react";
import { menuBarStateSelector } from "./menuBarState";

export const MenuBar = ({
    editor,
    onSave,
    onNewVersion,
    currentVersion,
    onLoadVersion,
    versions,
    onOpenLinkModal,
    profile,
    onProfileChange,
    onCompare,
    onOpenPreview,
}) => {
    const editorState = useEditorState({
        editor,
        selector: menuBarStateSelector,
    });

    if (!editor) return null;

    const isInTable = editor.isActive("table");

    return (
        <div className="control-group">
            <div className="button-group">
                {/* SAVE & VERSIONS & EXPORT */}
                <button type="button" onClick={onSave} title="Manual Save (Ctrl+S)" className="save-btn">
                    Save
                </button>
                <button type="button" onClick={onNewVersion} title="Create New Version" className="version-btn">
                    New Version
                </button>

                <select
                    value={currentVersion}
                    onChange={(e) => onLoadVersion(e.target.value)}
                    className="version-select"
                >
                    {versions.map(v => (
                        <option key={v.id} value={v.id}>
                            {v.id} ({v.isFormatted ? v.timestamp : new Date(v.timestamp).toLocaleString()})
                        </option>
                    ))}
                </select>

                <select
                    value={profile}
                    onChange={(e) => onProfileChange(e.target.value)}
                    className="version-select profile-select"
                >
                    <option value="Contract">Profile: Contract</option>
                    <option value="SOP">Profile: SOP</option>
                </select>

                {/* PDF & WORD & PRINT EXPORT */}
                <button
                    type="button"
                    onClick={onOpenPreview}
                    className="pdf-export-btn"
                    title="Export & Preview (Ctrl+P)"
                >
                    Preview & Export
                </button>


                {/* TEXT FORMATTING */}
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleBold().run()}
                    disabled={!editorState.canBold}
                    className={editorState.isBold ? "is-active" : ""}
                >
                    Bold
                </button>

                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleItalic().run()}
                    disabled={!editorState.canItalic}
                    className={editorState.isItalic ? "is-active" : ""}
                >
                    Italic
                </button>

                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleStrike().run()}
                    disabled={!editorState.canStrike}
                    className={editorState.isStrike ? "is-active" : ""}
                >
                    Strike
                </button>

                {/* HEADINGS */}
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                    className={editorState.isHeading1 ? "is-active" : ""}
                >
                    Heading 1
                </button>
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                    className={editorState.isHeading2 ? "is-active" : ""}
                >
                    Heading 2
                </button>
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
                    className={editorState.isHeading3 ? "is-active" : ""}
                >
                    Heading 3
                </button>

                {/* LISTS */}
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleBulletList().run()}
                    className={editorState.isBulletList ? "is-active" : ""}
                >
                    Bullet List
                </button>
                <button
                    type="button"
                    onClick={() => editor.chain().focus().toggleOrderedList().run()}
                    className={editorState.isOrderedList ? "is-active" : ""}
                >
                    Numbered List
                </button>

                {/* HISTORY */}
                <button
                    type="button"
                    onClick={() => editor.chain().focus().undo().run()}
                    disabled={!editorState.canUndo}
                >
                    Undo
                </button>
                <button
                    type="button"
                    onClick={() => editor.chain().focus().redo().run()}
                    disabled={!editorState.canRedo}
                >
                    Redo
                </button>


                {/* INSERT URL */}
                <button type="button" onClick={onOpenLinkModal} title="Insert Link (Ctrl+K)">
                    Insert URL
                </button>

                {/* DIFF VIEWER */}
                <button
                    onClick={() => {

                        if (versions.length < 2) return

                        const last = versions[versions.length - 1]
                        const prev = versions[versions.length - 2]

                        onCompare(prev.id, last.id)

                    }}
                >
                    Compare Last Versions
                </button>




                {/* TABLES */}
                <button
                    type="button"
                    onClick={() => editor.chain().focus().insertTable({ rows: 4, cols: 4, withHeaderRow: true }).run()}
                >
                    Insert Table
                </button>

                {isInTable && (
                    <>
                        <button type="button" onClick={() => editor.chain().focus().addColumnBefore().run()}>
                            Add Col Before
                        </button>
                        <button type="button" onClick={() => editor.chain().focus().addColumnAfter().run()}>
                            Add Col After
                        </button>
                        <button type="button" onClick={() => editor.chain().focus().deleteColumn().run()}>
                            Delete Column
                        </button>
                        <button type="button" onClick={() => editor.chain().focus().addRowBefore().run()}>
                            Add Row Before
                        </button>
                        <button type="button" onClick={() => editor.chain().focus().addRowAfter().run()}>
                            Add Row After
                        </button>
                        <button type="button" onClick={() => editor.chain().focus().deleteRow().run()}>
                            Delete Row
                        </button>
                        <button type="button" onClick={() => editor.chain().focus().deleteTable().run()}>
                            Delete Table
                        </button>
                    </>
                )}
            </div>
        </div>
    );
};
export default MenuBar;