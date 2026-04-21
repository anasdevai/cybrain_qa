/**
 * PlaceholderHighlight.js
 * 
 * This Tiptap extension automatically highlights placeholder variables written in 
 * the format {{variable_name}} within the editor. It uses ProseMirror decorations 
 * to apply styles without altering the actual document schema or HTML structure.
 */

import { Extension } from '@tiptap/core';
import { Plugin } from 'prosemirror-state';
import { Decoration, DecorationSet } from 'prosemirror-view';

// Regular expression to match variable placeholders. 
// It looks for a sequence of alphanumeric characters or underscores enclosed in double curly braces {{ }}.
const PLACEHOLDER_REGEX = /\{\{([A-Za-z0-9_]+)\}\}/g;

/**
 * Traverses the document to find placeholder matches and creates inline decorations for them.
 * 
 * @param {Node} doc - The ProseMirror document node to scan for placeholders.
 * @returns {DecorationSet} A collection of ProseMirror decorations highlighting the placeholders.
 */
function createPlaceholderDecorations(doc) {
    const decorations = [];

    // Iterate over all nodes in the document
    doc.descendants((node, pos) => {
        // We only care about text nodes, as placeholders are text-based
        if (!node.isText || !node.text) return;

        const text = node.text;
        let match;

        // Execute regex search over the text node's content
        while ((match = PLACEHOLDER_REGEX.exec(text)) !== null) {
            const start = pos + match.index; // Start position of the placeholder in the document
            const end = start + match[0].length; // End position of the placeholder

            // Create an inline decoration for the matched text
            decorations.push(
                Decoration.inline(start, end, {
                    class: 'placeholder-variable', // CSS class used for styling
                    'data-placeholder-name': match[1], // Store the exact variable name in a data attribute
                })
            );
        }

        // Reset the regex state to safely reuse it on the next text node
        PLACEHOLDER_REGEX.lastIndex = 0;
    });

    // Return the generated set of decorations
    return DecorationSet.create(doc, decorations);
}

/**
 * PlaceholderHighlight Extension
 * 
 * Registers a Tiptap extension that injects a ProseMirror plugin to handle
 * the real-time application and updating of placeholder decorations.
 */
export const PlaceholderHighlight = Extension.create({
    name: 'placeholderHighlight',

    // Add required ProseMirror plugins to the editor
    addProseMirrorPlugins() {
        return [
            new Plugin({
                state: {
                    // Initialize the decorations when the plugin is first loaded
                    init(_, { doc }) {
                        return createPlaceholderDecorations(doc);
                    },
                    // Update decorations whenever the document state changes via transactions
                    apply(tr, oldDecorationSet) {
                        // Optimization: Skip recalculation if the document hasn't changed
                        if (!tr.docChanged) return oldDecorationSet;
                        
                        // Re-generate decorations for the new document state
                        return createPlaceholderDecorations(tr.doc);
                    },
                },
                props: {
                    // Provide the decorations from the plugin state to the view
                    decorations(state) {
                        return this.getState(state);
                    },
                },
            }),
        ];
    },
});