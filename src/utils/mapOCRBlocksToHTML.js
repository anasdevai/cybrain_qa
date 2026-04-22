const escapeHtml = (text = '') =>
    String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

const cleanText = (text = '') => {
    return String(text)
        .replace(/\r\n/g, '\n')
        .replace(/\r/g, '\n')
        .replace(/[ \t]+/g, ' ')
        .replace(/\n{3,}/g, '\n\n')
        .trim();
};

const splitParagraphs = (text = '') => {
    const cleaned = cleanText(text);
    if (!cleaned) return [];
    return cleaned
        .split(/\n{2,}/)
        .map((part) => cleanText(part))
        .filter(Boolean);
};

const splitLines = (text = '') => {
    const cleaned = cleanText(text);
    if (!cleaned) return [];
    return cleaned
        .split('\n')
        .map((line) => cleanText(line))
        .filter(Boolean);
};

const normalizeItems = (items) => {
    if (!Array.isArray(items)) return [];
    return items
        .map((item) => cleanText(item))
        .filter(Boolean);
};

const renderParagraphs = (text = '', className = '') => {
    const paragraphs = splitParagraphs(text);
    if (!paragraphs.length) return '';

    return paragraphs
        .map((p) => `<p${className ? ` class="${className}"` : ''}>${escapeHtml(p)}</p>`)
        .join('');
};

const renderList = (items = [], ordered = false, className = '') => {
    const validItems = normalizeItems(items);
    if (!validItems.length) return '';

    const tag = ordered ? 'ol' : 'ul';

    return `
    <${tag}${className ? ` class="${className}"` : ''}>
      ${validItems.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
    </${tag}>
  `;
};

const renderTwoColumnRow = (block, isContract) => {
    const left = cleanText(block.left || '');
    const right = cleanText(block.right || '');

    if (!left && !right) return '';

    if (isContract) {
        return `
      <div class="ocr-two-col-row">
        <div class="ocr-two-col-left">${escapeHtml(left)}</div>
        <div class="ocr-two-col-right">${escapeHtml(right)}</div>
      </div>
    `;
    }

    if (left && right) {
        return `<p class="ocr-key-value"><strong>${escapeHtml(left)}:</strong> ${escapeHtml(right)}</p>`;
    }

    return `<p>${escapeHtml(left || right)}</p>`;
};

const renderTable = (block = {}) => {
    const rows = Array.isArray(block.rows) ? block.rows : [];
    if (!rows.length) return '';

    const normalizedRows = rows
        .map((row) => (Array.isArray(row) ? row.map((cell) => cleanText(cell || '')) : []))
        .filter((row) => row.some(Boolean));

    if (!normalizedRows.length) return '';

    return `
    <table class="ocr-table">
      <tbody>
        ${normalizedRows
            .map(
                (row) => `
              <tr>
                ${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join('')}
              </tr>
            `
            )
            .join('')}
      </tbody>
    </table>
  `;
};

const renderBlock = (block = {}, isContract = false) => {
    if (!block || typeof block !== 'object') return '';

    const type = String(block.type || 'paragraph').toLowerCase();
    const text = cleanText(block.text || '');

    switch (type) {
        case 'title':
            return text ? `<h1 class="ocr-title">${escapeHtml(text)}</h1>` : '';

        case 'section_heading':
            return text ? `<h2 class="ocr-section-heading">${escapeHtml(text)}</h2>` : '';

        case 'heading':
        case 'subheading':
            return text ? `<h3 class="ocr-heading">${escapeHtml(text)}</h3>` : '';

        case 'paragraph':
            return renderParagraphs(text);

        case 'note':
            return renderParagraphs(text, 'ocr-note');

        case 'quote':
        case 'blockquote':
            return text ? `<blockquote class="ocr-quote">${escapeHtml(text)}</blockquote>` : '';

        case 'two_column_row':
        case 'key_value':
            return renderTwoColumnRow(block, isContract);

        case 'list':
        case 'bullet_list':
            return renderList(block.items || splitLines(text), false, 'ocr-list');

        case 'numbered_list':
        case 'ordered_list':
            return renderList(block.items || splitLines(text), true, 'ocr-list ocr-list-ordered');

        case 'table':
            return renderTable(block);

        case 'divider':
        case 'horizontal_rule':
            return `<hr class="ocr-divider" />`;

        case 'line':
            return text ? `<p class="ocr-line">${escapeHtml(text)}</p>` : '';

        default:
            return text ? renderParagraphs(text) : '';
    }
};

export const mapOCRBlocksToHTML = (blocks = [], profile = 'simple') => {
    if (!Array.isArray(blocks) || !blocks.length) return '';

    const isContract = String(profile || '').toLowerCase() === 'contract';

    const html = blocks
        .map((block) => renderBlock(block, isContract))
        .filter(Boolean)
        .join('');

    return html || '<p></p>';
};