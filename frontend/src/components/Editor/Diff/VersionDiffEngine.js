/**
 * VersionDiffEngine.js
 * 
 * Core logic for comparing two Tiptap document JSON structures.
 * It identifies additions, deletions, and modifications at the block level
 * (paragraphs, headings, tables) based on unique 'block-id' attributes.
 */

import { compareBlocks } from './BlockComparator';
import { compareTableNodes } from './TableComparator';

/**
 * Creates a fast-lookup map of block IDs to their respective node objects.
 * @param {Array} contentArray - Array of ProseMirror/Tiptap node objects.
 * @returns {Map} A Map where keys are block-ids and values are the nodes.
 */
const buildIdMap = (contentArray = []) => {
    const map = new Map();
    contentArray.forEach(node => {
        const blockId = node?.attrs?.['block-id'];
        if (blockId) map.set(blockId, node);
    });
    return map;
};

/**
 * Compares an old document JSON against a new document JSON to generate a unified 
 * difference view structure. Iterates through the new document to find matches in 
 * the old document, falling back to marking nodes as 'added' or 'removed'.
 * 
 * @param {Object} oldJson - The baseline Tiptap document JSON.
 * @param {Object} newJson - The current/target Tiptap document JSON.
 * @returns {Object} A new document JSON structurally containing 'diffStatus' metadata.
 */
export const generateDocumentDiff = (oldJson, newJson) => {
    // Return empty document if either input is invalid
    if (!oldJson || !newJson) return { type: 'doc', content: [] };

    const oldContent = oldJson.content || [];
    const newContent = newJson.content || [];

    // Map old nodes by their block-id for O(1) lookups
    const oldMap = buildIdMap(oldContent);
    // Track which old nodes have been checked to find deletions later
    const processedOldIds = new Set();
    const diffResult = [];

    // 1. Iterate through new content to find additions and modifications
    newContent.forEach((newNode) => {
        const blockId = newNode?.attrs?.['block-id'];

        // Handle complex Table nodes separately
        if (newNode.type === 'table') {
            const oldNode = blockId ? oldMap.get(blockId) : null;

            if (oldNode) {
                processedOldIds.add(blockId);
                const tableDiff = compareTableNodes(oldNode, newNode);
                diffResult.push(tableDiff.isChanged ? { ...tableDiff.node, diffStatus: 'modified' } : newNode);
            } else {
                diffResult.push({ ...newNode, diffStatus: 'added' });
            }
            return;
        }

        // Handle standard blocks (paragraphs, headings, lists)
        if (blockId) {
            const oldNode = oldMap.get(blockId);

            if (oldNode) {
                processedOldIds.add(blockId);
                const diff = compareBlocks(oldNode, newNode);
                diffResult.push(diff.isChanged ? { ...diff.node, diffStatus: 'modified' } : newNode);
            } else {
                diffResult.push({ ...newNode, diffStatus: 'added' });
            }
            return;
        }

        // Nodes without block-ids (rare/fallback) are marked as added
        diffResult.push({ ...newNode, diffStatus: 'added' });
    });

    // 2. Identify and append removed blocks from the old content
    oldContent.forEach((oldNode) => {
        const blockId = oldNode?.attrs?.['block-id'];
        // If an old block was not processed, it means it was deleted in the new version
        if (blockId && !processedOldIds.has(blockId)) {
            diffResult.push({ ...oldNode, diffStatus: 'removed' });
        }
    });

    return { type: 'doc', content: diffResult };
};
