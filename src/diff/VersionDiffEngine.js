import { compareBlocks } from './BlockComparator';
import { compareTableNodes } from './TableComparator';

const buildIdMap = (contentArray = []) => {
    const map = new Map();
    contentArray.forEach(node => {
        const blockId = node?.attrs?.['block-id'];
        if (blockId) map.set(blockId, node);
    });
    return map;
};

export const generateDocumentDiff = (oldJson, newJson) => {
    if (!oldJson || !newJson) return { type: 'doc', content: [] };

    const oldContent = oldJson.content || [];
    const newContent = newJson.content || [];

    const oldMap = buildIdMap(oldContent);
    const processedOldIds = new Set();
    const diffResult = [];

    newContent.forEach((newNode) => {
        const blockId = newNode?.attrs?.['block-id'];

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

        diffResult.push({ ...newNode, diffStatus: 'added' });
    });

    oldContent.forEach((oldNode) => {
        const blockId = oldNode?.attrs?.['block-id'];
        if (blockId && !processedOldIds.has(blockId)) {
            diffResult.push({ ...oldNode, diffStatus: 'removed' });
        }
    });

    return { type: 'doc', content: diffResult };
};