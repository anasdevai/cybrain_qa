import { compareBlocks } from './BlockComparator';
import { compareTableNodes } from './TableComparator';

// Helper to build a map of block-ids
const buildIdMap = (contentArray, map = new Map()) => {
    if (!contentArray || !Array.isArray(contentArray)) return map;

    contentArray.forEach(node => {
        if (node.attrs && node.attrs['block-id']) {
            map.set(node.attrs['block-id'], node);
        }
        // Descend into node content (useful for nested block-ids, though tip-tap usually keeps them top level)
        if (node.content && node.type !== 'table') {
            buildIdMap(node.content, map);
        }
    });
    return map;
};

export const generateDocumentDiff = (oldJson, newJson) => {
    if (!oldJson || !newJson) return { content: [] };

    const oldContent = oldJson.content || [];
    const newContent = newJson.content || [];

    const oldMap = buildIdMap(oldContent);
    const newMap = buildIdMap(newContent);

    const diffResult = [];

    // 1. Process new document content (handles unchanged, modified, and added blocks)
    newContent.forEach(newNode => {
        const blockId = newNode.attrs ? newNode.attrs['block-id'] : null;

        if (newNode.type === 'table') {
            // Tables don't always have block-ids, but we handle them specialized
            // We'll try to find a matching old table by index for simplicity if no block-id exists
            // This is a naive table matching. A robust version would match by proximity or block-id if tables are allowed them.
            const oldNode = blockId ? oldMap.get(blockId) : oldContent.find(n => n.type === 'table' && JSON.stringify(n) !== JSON.stringify(newNode));

            if (oldNode) {
                const tableDiff = compareTableNodes(oldNode, newNode);
                diffResult.push(tableDiff.isChanged ? { ...tableDiff.node, diffStatus: 'modified' } : newNode);
                if (blockId) oldMap.delete(blockId);
            } else {
                diffResult.push({ ...newNode, diffStatus: 'added' });
            }
        }
        else if (blockId) {
            const oldNode = oldMap.get(blockId);

            if (oldNode) {
                // Block exists in both. Compare them.
                const diff = compareBlocks(oldNode, newNode);

                if (diff.isChanged) {
                    diffResult.push({ ...diff.node, diffStatus: 'modified' });
                } else {
                    diffResult.push(newNode); // unchanged
                }

                // We've processed this old node
                oldMap.delete(blockId);
            } else {
                // Block is in new, but not in old
                diffResult.push({ ...newNode, diffStatus: 'added' });
            }
        } else {
            // Node has no blockId (e.g., raw text row or unconfigured extensions).
            // Default to seeing if an exact match exists.
            const exactMatch = oldContent.find(n => JSON.stringify(n) === JSON.stringify(newNode));
            if (exactMatch) {
                diffResult.push(newNode);
            } else {
                diffResult.push({ ...newNode, diffStatus: 'added' });
            }
        }
    });

    // 2. Process remaining old content (these are removed blocks)
    // We insert them at the end of the document, or ideally close to where they were.
    // For simplicity, we append them at the end, but UI will show them as removed.
    oldMap.forEach((oldNode, blockId) => {
        diffResult.push({ ...oldNode, diffStatus: 'removed' });
    });

    return { type: 'doc', content: diffResult };
};
