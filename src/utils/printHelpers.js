import { resolveTextWithVariables } from './resolveVariables';

export const buildCleanExportHtml = (resolvedContent) => {
  const parser = new DOMParser();
  const doc = parser.parseFromString(resolvedContent, 'text/html');

  doc.querySelectorAll('[block-id]').forEach((el) => {
    el.removeAttribute('block-id');
  });

  doc.querySelectorAll('.column-resize-handle').forEach((el) => el.remove());

  doc.querySelectorAll('.selectedCell').forEach((el) => {
    el.classList.remove('selectedCell');
  });

  doc.querySelectorAll('table').forEach((table) => {
    table.style.borderCollapse = 'collapse';
    table.style.width = '100%';
    table.style.tableLayout = 'fixed';
    table.style.margin = '24px 0';
  });

  doc.querySelectorAll('th, td').forEach((cell) => {
    cell.style.border = '1px solid #444';
    cell.style.padding = '8px 10px';
    cell.style.verticalAlign = 'top';
    cell.style.textAlign = 'left';
    cell.style.wordBreak = 'break-word';
  });

  doc.querySelectorAll('th').forEach((th) => {
    th.style.fontWeight = '600';
    th.style.backgroundColor = '#f8fafc';
  });

  doc.querySelectorAll('img').forEach((img) => {
    img.style.maxWidth = '100%';
    img.style.height = 'auto';
  });

  return doc.body.innerHTML;
};

export const printDocument = (editorHtml, variables, orientation = 'portrait') => {
  const resolvedContent = resolveTextWithVariables(editorHtml, variables);
  const cleanContent = buildCleanExportHtml(resolvedContent);
  const printWindow = window.open('', '_blank');

  if (!printWindow) return;

  printWindow.document.write(`
      <html>
        <head>
          <title>Print Document</title>
          <style>
            @page {
              margin: 20mm;
              size: A4 ${orientation};
            }
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              padding: 0;
              margin: 0;
              color: #000;
            }
            .tiptap {
              line-height: 1.6;
              font-size: 12pt;
              max-width: 100%;
              word-break: break-word;
            }
            table {
              border-collapse: collapse;
              width: 100%;
              table-layout: fixed;
              margin: 1.5em 0;
              page-break-inside: auto;
            }
            tr {
              page-break-inside: avoid;
              page-break-after: auto;
            }
            th, td {
              border: 1px solid #000;
              padding: 8px 12px;
              text-align: left;
              vertical-align: top;
              word-break: break-word;
            }
            th {
              background-color: #f8fafc !important;
              -webkit-print-color-adjust: exact;
              print-color-adjust: exact;
              font-weight: bold;
            }
            img {
              max-width: 100%;
              height: auto;
            }
          </style>
        </head>
        <body>
          <div class="tiptap">${cleanContent}</div>
          <script>
            window.onload = () => {
              setTimeout(() => {
                window.print();
                window.close();
              }, 300);
            };
          </script>
        </body>
      </html>
    `);

  printWindow.document.close();
};
