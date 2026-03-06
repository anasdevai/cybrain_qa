import { diffWords } from 'diff';

// A simple utility to get plain text from a node's content array
export const extractTextFromNode = (node) => {
    if (!node) return '';
    if (node.type === 'text') return node.text || '';
    if (node.content && Array.isArray(node.content)) {
        return node.content.map(extractTextFromNode).join('');
    }
    return '';
};

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
