/**
 * TableComparator.js
 * 
 * Contains custom diffing logic specifically designed for Tiptap Table, TableRow, 
 * and TableCell nodes. It iterates through the grid to identify added, removed, 
 * or modified rows and cells to inject correct diffStatus metadata.
 */
import { compareBlocks } from './BlockComparator';

/**
 * Compares two table nodes traversing rows and columns to find differences.
 * 
 * @param {Object} oldTable - The Table node from the older document version.
 * @param {Object} newTable - The Table node from the newer document version.
 * @returns {Object} An object indicating if a change occurred alongside the annotated diff table node.
 */
export const compareTableNodes = (oldTable, newTable) => {
    // If exact same table reference or structurally identical strings
    if (JSON.stringify(oldTable) === JSON.stringify(newTable)) {
        return { isChanged: false, node: newTable };
    }

    const diffTable = { ...newTable };
    diffTable.content = [];

    // Simple row-by-row and cell-by-cell comparison.
    // If rows/cols are added or removed, we highlight the new/old cells.
    const oldRows = oldTable.content || [];
    const newRows = newTable.content || [];

    const maxRows = Math.max(oldRows.length, newRows.length);

    for (let i = 0; i < maxRows; i++) {
        const oldRow = oldRows[i];
        const newRow = newRows[i];

        if (!oldRow && newRow) {
            // Row added - append to diff marking it as new
            diffTable.content.push({ ...newRow, diffStatus: 'added' });
        } else if (oldRow && !newRow) {
            // Row removed - push the old row so the viewer can render it as deleted (red block)
            diffTable.content.push({ ...oldRow, diffStatus: 'removed' });
        } else {
            // Compare cells within the row
            const diffRow = { ...newRow, content: [] };
            const oldCells = oldRow.content || [];
            const newCells = newRow.content || [];
            const maxCols = Math.max(oldCells.length, newCells.length);

            for (let j = 0; j < maxCols; j++) {
                const oldCell = oldCells[j];
                const newCell = newCells[j];

                if (!oldCell && newCell) {
                    // Entire column/cell added
                    diffRow.content.push({ ...newCell, diffStatus: 'added' });
                } else if (oldCell && !newCell) {
                    // Entire column/cell removed
                    diffRow.content.push({ ...oldCell, diffStatus: 'removed' });
                } else {
                    // Both cells exist, compare them block by block using the text diff utility
                    const blockDiff = compareBlocks(oldCell, newCell);
                    if (blockDiff.isChanged) {
                        // The cell has changed internal text
                        diffRow.content.push({ ...blockDiff.node, diffStatus: 'modified' });
                    } else {
                        // No changes inside this cell
                        diffRow.content.push(newCell);
                    }
                }
            }
            diffTable.content.push(diffRow);
        }
    }

    return { isChanged: true, node: diffTable };
};
