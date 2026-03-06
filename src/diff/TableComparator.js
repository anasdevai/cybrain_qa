import { compareBlocks } from './BlockComparator';

export const compareTableNodes = (oldTable, newTable) => {
    // If exact same table
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
            // Row added
            diffTable.content.push({ ...newRow, diffStatus: 'added' });
        } else if (oldRow && !newRow) {
            // Row removed, we actually push the old row so the viewer can render it as removed
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
                    diffRow.content.push({ ...newCell, diffStatus: 'added' });
                } else if (oldCell && !newCell) {
                    diffRow.content.push({ ...oldCell, diffStatus: 'removed' });
                } else {
                    // Both cells exist, compare them block by block
                    const blockDiff = compareBlocks(oldCell, newCell);
                    if (blockDiff.isChanged) {
                        // The cell has changed internal text
                        diffRow.content.push({ ...blockDiff.node, diffStatus: 'modified' });
                    } else {
                        diffRow.content.push(newCell);
                    }
                }
            }
            diffTable.content.push(diffRow);
        }
    }

    return { isChanged: true, node: diffTable };
};
