/**
 * menuBarState.js
 * 
 * Provides a highly optimized selector function for Tiptap's `useEditorState` hook.
 * Instead of re-rendering the entire MenuBar on every single keystroke or selection change,
 * this selector extracts only the specific boolean states needed by the toolbar buttons
 * (e.g., is bold active? can we undo?).
 */

/**
 * Maps the current Tiptap editor context to a flat state object.
 * 
 * @param {Object} ctx - The Tiptap editor context.
 * @returns {Object} An object containing boolean flags for formatting and history states.
 */
export function menuBarStateSelector(ctx) {
    return {
        // TEXT FORMATTING
        isBold: ctx.editor.isActive('bold') ?? false,
        canBold: ctx.editor.can().chain().toggleBold().run() ?? false,

        isItalic: ctx.editor.isActive('italic') ?? false,
        canItalic: ctx.editor.can().chain().toggleItalic().run() ?? false,

        isUnderline: ctx.editor.isActive('underline') ?? false,
        canUnderline: ctx.editor.can().chain().toggleUnderline().run() ?? false,

        isStrike: ctx.editor.isActive('strike') ?? false,
        canStrike: ctx.editor.can().chain().toggleStrike().run() ?? false,

        // BLOCK TYPES
        isHeading1: ctx.editor.isActive('heading', { level: 1 }) ?? false,
        isHeading2: ctx.editor.isActive('heading', { level: 2 }) ?? false,
        isHeading3: ctx.editor.isActive('heading', { level: 3 }) ?? false,

        // LISTS
        isBulletList: ctx.editor.isActive('bulletList') ?? false,
        isOrderedList: ctx.editor.isActive('orderedList') ?? false,

        // HISTORY
        canUndo: ctx.editor.can().chain().undo().run() ?? false,
        canRedo: ctx.editor.can().chain().redo().run() ?? false,
    }
}