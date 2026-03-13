/**
 * BlockComparator.js
 * 
 * Provides utility functions for comparing corresponding text blocks
 * (e.g., paragraphs or list items) between two different document versions.
 * Uses the external `diff` package to compute word-level changes.
 */

import { diffWords } from 'diff';

/**
 * Recursively extracts plain text from a parsed Tiptap node and its children.
 * @param {Object} node - A Tiptap document block node.
 * @returns {string} The aggregated plain string text.
 */
export const extractTextFromNode = (node) => {
    if (!node) return '';
    if (node.type === 'text') return node.text || '';
    if (node.content && Array.isArray(node.content)) {
        return node.content.map(extractTextFromNode).join('');
    }
    return '';
};

/**
 * Compares two corresponding blocks (matched via ID) from different versions
 * and generates a structured difference map separating words into added, removed, or unmodified.
 * 
 * @param {Object} oldNode - The block from the older document version.
 * @param {Object} newNode - The block from the newer document version.
 * @returns {Object} An object indicating if a change occurred and a special diff container node.
 */
export const compareBlocks = (oldNode, newNode) => {
    // If they are exactly the same reference or stringified exactly the same
    if (JSON.stringify(oldNode) === JSON.stringify(newNode)) {
        return { isChanged: false, node: newNode };
    }

    const oldText = extractTextFromNode(oldNode);
    const newText = extractTextFromNode(newNode);

    // If text is unchanged but maybe formatting changed, we'll still flag as changed 
    // but the word-level diff won't highlight red/green words.
    // For universal editor, we prioritize text diffs.
    const differences = diffWords(oldText, newText);

    // We reconstruct a special node to send to the renderer
    // We will inject a structure the DiffViewer can interpret.
    const diffNode = {
        ...newNode,
        isDiffContainer: true,
        diffs: differences.map(part => ({
            value: part.value,
            added: part.added || false,
            removed: part.removed || false
        }))
    };

    return { isChanged: true, node: diffNode };
};