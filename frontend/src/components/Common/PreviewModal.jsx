/**
 * PreviewModal.jsx
 * 
 * Provides a modal dialog that renders the current document in a paginated, 
 * print-ready preview format. It also supplies functionality to export the 
 * document as a pristine PDF or a styled Word Document (.doc format).
 */

import React, { useRef, useState } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { resolveTextWithVariables } from '../../utils/resolveVariables';
import { printDocument } from '../../utils/printHelpers';

import { useLanguage } from '../../context/LanguageContext';

/**
 * Preview and Export Modal Component.
 * @param {Object} props
 * @param {boolean} props.isOpen - Determines if the modal is currently visible.
 * @param {Function} props.onClose - Triggered to close the modal.
 * @param {Object} props.editor - Tiptap editor instance containing the content.
 * @param {string} props.versionId - Version label used for naming exported files.
 * @param {Object} props.contractVariables - Map of variable keys to user inputs for placeholder interpolation.
 */
const PreviewModal = ({
    isOpen,
    onClose,
    editor,
    versionId,
    contractVariables = {},
}) => {
    const previewRef = useRef(null);
    const { t } = useLanguage();
    const [scale, setScale] = useState(1);
    const [orientation, setOrientation] = useState('portrait');

    if (!isOpen || !editor) return null;

    // Raw HTML exported from the editor instance
    const rawContent = editor.getHTML();
    // HTML where all {{variable}} placeholders are substituted with actual string values
    const resolvedContent = resolveTextWithVariables(rawContent, contractVariables);

    /**
     * Parses the rendered HTML and meticulously cleans up UI-specific classes, 
     * metadata attributes, and applies strict inline styling suitable for raw physical printing or PDF export.
     * @returns {string} Sanitized, print-ready HTML string.
     */
    const buildCleanExportHtml = () => {
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

    /**
     * Constructs a hidden div floating off-screen to mount the cleaned HTML.
     * This forces the browser to render the exact pixel layout of the document 
     * so that `html2canvas` can accurately capture a screenshot of it for the PDF.
     * @returns {HTMLElement} A DOM node containing the fully styled print preview block.
     */
    const buildExportContainer = () => {
        const cleanContent = buildCleanExportHtml();

        const exportWrapper = document.createElement('div');
        exportWrapper.innerHTML = `<div class="tiptap">${cleanContent}</div>`;

        exportWrapper.style.position = 'fixed';
        exportWrapper.style.top = '0';
        exportWrapper.style.left = '-10000px';
        exportWrapper.style.background = '#ffffff';
        exportWrapper.style.color = '#000000';
        exportWrapper.style.boxSizing = 'border-box';
        exportWrapper.style.fontFamily = 'Arial, sans-serif';
        exportWrapper.style.fontSize = '12pt';
        exportWrapper.style.lineHeight = '1.6';
        exportWrapper.style.width = orientation === 'portrait' ? '794px' : '1123px';
        exportWrapper.style.minHeight = orientation === 'portrait' ? '1123px' : '794px';
        exportWrapper.style.padding = '76px';
        exportWrapper.style.zIndex = '-1';
        exportWrapper.style.pointerEvents = 'none';

        const tiptap = exportWrapper.querySelector('.tiptap');
        if (tiptap) {
            tiptap.style.fontFamily = 'Arial, sans-serif';
            tiptap.style.fontSize = '12pt';
            tiptap.style.lineHeight = '1.6';
            tiptap.style.color = '#000';
            tiptap.style.wordBreak = 'break-word';
        }

        exportWrapper.querySelectorAll('h1').forEach((el) => {
            el.style.fontSize = '24pt';
            el.style.fontWeight = '700';
            el.style.margin = '0 0 16px 0';
            el.style.lineHeight = '1.25';
        });

        exportWrapper.querySelectorAll('h2').forEach((el) => {
            el.style.fontSize = '18pt';
            el.style.fontWeight = '700';
            el.style.margin = '20px 0 12px 0';
            el.style.lineHeight = '1.3';
        });

        exportWrapper.querySelectorAll('h3').forEach((el) => {
            el.style.fontSize = '14pt';
            el.style.fontWeight = '700';
            el.style.margin = '16px 0 10px 0';
            el.style.lineHeight = '1.35';
        });

        exportWrapper.querySelectorAll('p').forEach((el) => {
            el.style.margin = '0 0 12px 0';
        });

        exportWrapper.querySelectorAll('ul, ol').forEach((el) => {
            el.style.margin = '0 0 12px 24px';
            el.style.padding = '0';
        });

        exportWrapper.querySelectorAll('li').forEach((el) => {
            el.style.margin = '0 0 6px 0';
        });

        exportWrapper.querySelectorAll('table').forEach((table) => {
            table.style.borderCollapse = 'collapse';
            table.style.width = '100%';
            table.style.tableLayout = 'fixed';
            table.style.margin = '20px 0';
            table.style.fontSize = '11pt';
        });

        exportWrapper.querySelectorAll('th, td').forEach((cell) => {
            cell.style.border = '1px solid #000';
            cell.style.padding = '8px';
            cell.style.textAlign = 'left';
            cell.style.verticalAlign = 'top';
            cell.style.wordBreak = 'break-word';
        });

        exportWrapper.querySelectorAll('th').forEach((th) => {
            th.style.backgroundColor = '#f3f4f6';
            th.style.fontWeight = '700';
        });

        exportWrapper.querySelectorAll('strong').forEach((el) => {
            el.style.fontWeight = '700';
        });

        exportWrapper.querySelectorAll('em').forEach((el) => {
            el.style.fontStyle = 'italic';
        });

        exportWrapper.querySelectorAll('u').forEach((el) => {
            el.style.textDecoration = 'underline';
        });

        exportWrapper.querySelectorAll('s').forEach((el) => {
            el.style.textDecoration = 'line-through';
        });

        exportWrapper.querySelectorAll('a').forEach((el) => {
            el.style.color = '#0000EE';
            el.style.textDecoration = 'underline';
        });

        exportWrapper.querySelectorAll('img').forEach((img) => {
            img.style.maxWidth = '100%';
            img.style.height = 'auto';
        });

        return exportWrapper;
    };

    /**
     * Triggered when the user clicks 'Print'. Opens an invisible/temporary popup window,
     * writes the cleaned HTML into it with specific `@page` CSS directives, and automatically fires the browser print dialog.
     */
    const handlePrint = () => {
        printDocument(editor.getHTML(), contractVariables, orientation);
    };

    /**
     * Asynchronous PDF generation routine. Captures the hidden off-screen layout via `html2canvas`,
     * converts the canvas to an image, calculates paginations based on the specified orientation,
     * builds the pages in `jsPDF`, and triggers a file download.
     */
    const handleExportPDF = async () => {
        const exportWrapper = buildExportContainer();
        document.body.appendChild(exportWrapper);

        try {
            await new Promise((resolve) => setTimeout(resolve, 300));

            const canvas = await html2canvas(exportWrapper, {
                scale: 3,
                useCORS: true,
                backgroundColor: '#ffffff',
                logging: false,
            });

            const pdf = new jsPDF({
                orientation,
                unit: 'mm',
                format: 'a4',
            });

            const pageWidth = orientation === 'portrait' ? 210 : 297;
            const pageHeight = orientation === 'portrait' ? 297 : 210;

            const imgData = canvas.toDataURL('image/png');
            const imgWidth = pageWidth;
            const imgHeight = (canvas.height * imgWidth) / canvas.width;

            let heightLeft = imgHeight;
            let position = 0;

            pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;

            while (heightLeft > 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;
            }

            pdf.save(`Document-${versionId}.pdf`);
        } catch (error) {
            console.error('PDF export failed:', error);
            alert('PDF export failed. Check console for details.');
        } finally {
            document.body.removeChild(exportWrapper);
        }
    };

    /**
     * Converts the editor content into an encapsulated HTML document structure 
     * that Microsoft Word can interpret natively, adds `.doc` mime-types, and initiates a download.
     */
    const handleExportWord = () => {
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
            table.setAttribute('border', '1');
            table.setAttribute('cellpadding', '8');
            table.setAttribute('cellspacing', '0');
            table.style.borderCollapse = 'collapse';
            table.style.width = '100%';
            table.style.tableLayout = 'fixed';
            table.style.marginBottom = '20px';
        });

        doc.querySelectorAll('th, td').forEach((cell) => {
            cell.style.border = '1px solid black';
            cell.style.padding = '8px';
            cell.style.textAlign = 'left';
            cell.style.verticalAlign = 'top';
            cell.style.wordBreak = 'break-word';
        });

        doc.querySelectorAll('th').forEach((th) => {
            th.style.backgroundColor = '#f3f4f6';
            th.style.fontWeight = 'bold';
        });

        doc.querySelectorAll('img').forEach((img) => {
            img.style.maxWidth = '100%';
            img.style.height = 'auto';
        });

        const modifiedContent = doc.body.innerHTML;

        const header =
            "<html xmlns:o='urn:schemas-microsoft-com:office:office' " +
            "xmlns:w='urn:schemas-microsoft-com:office:word' " +
            "xmlns='http://www.w3.org/TR/REC-html40'>" +
            "<head><meta charset='utf-8'><title>Export Word</title>" +
            "<style>" +
            "body { font-family: Arial, sans-serif; line-height: 1.6; }" +
            "table { border-collapse: collapse; width: 100%; table-layout: fixed; }" +
            "th, td { border: 1px solid #000; padding: 8px; vertical-align: top; }" +
            "img { max-width: 100%; height: auto; }" +
            "</style>" +
            "</head><body>";

        const footer = '</body></html>';
        const sourceHTML = header + modifiedContent + footer;

        const source =
            'data:application/vnd.ms-word;charset=utf-8,' +
            encodeURIComponent(sourceHTML);

        const fileDownload = document.createElement('a');
        document.body.appendChild(fileDownload);
        fileDownload.href = source;
        fileDownload.download = `Document-${versionId}.doc`;
        fileDownload.click();
        document.body.removeChild(fileDownload);
    };

    return (
        <div className="link-modal-overlay" onClick={onClose}>
            <div
                className="link-modal preview-modal"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="link-modal-header">
                    <h3>{t.printPreviewExport}</h3>
                    <button
                        type="button"
                        className="close-btn"
                        onClick={onClose}
                    >
                        &times;
                    </button>
                </div>

                <div className="preview-toolbar">
                    <div className="toolbar-group">
                        <label>{t.orientation}</label>
                        <select
                            value={orientation}
                            onChange={(e) => setOrientation(e.target.value)}
                        >
                            <option value="portrait">{t.portrait}</option>
                            <option value="landscape">{t.landscape}</option>
                        </select>
                    </div>

                    <div className="toolbar-group">
                        <label>{t.zoom}</label>
                        <input
                            type="range"
                            min="0.5"
                            max="1.5"
                            step="0.1"
                            value={scale}
                            onChange={(e) => setScale(parseFloat(e.target.value))}
                        />
                    </div>
                </div>

                <div className="preview-content-wrapper">
                    <div
                        ref={previewRef}
                        className={`preview-page-container ${orientation}`}
                        style={{
                            zoom: scale,
                            marginLeft: 'auto',
                            marginRight: 'auto',
                        }}
                    >
                        <div
                            className="tiptap preview-content"
                            dangerouslySetInnerHTML={{ __html: resolvedContent }}
                        />
                    </div>
                </div>

                <div className="link-modal-footer">
                    <button
                        type="button"
                        className="cancel-btn"
                        onClick={handlePrint}
                    >
                        {t.print}
                    </button>
                    <button
                        type="button"
                        className="ok-btn word-btn"
                        onClick={handleExportWord}
                    >
                        {t.exportWord}
                    </button>
                    <button
                        type="button"
                        className="ok-btn"
                        onClick={handleExportPDF}
                    >
                        {t.exportPdf}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PreviewModal;