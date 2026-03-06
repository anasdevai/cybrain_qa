import React, { useMemo } from 'react';
import { generateDocumentDiff } from './VersionDiffEngine';
import './SideBySideViewer.css';

// A recursive renderer that walks the specialized diff AST
const DiffNodeRenderer = ({ node }) => {
    if (!node) return null;

    const { type, text, attrs, content, diffStatus, isDiffContainer, diffs } = node;

    // Apply color coding based on diff status
    let className = 'diff-node';
    if (diffStatus === 'added') className += ' diff-added';
    if (diffStatus === 'removed') className += ' diff-removed';
    if (diffStatus === 'modified') className += ' diff-modified';

    // 1. Text Node Handlers
    if (type === 'text') {
        return <span className={className}>{text}</span>;
    }

    // 2. Specialized Word-Level Diff Nodes (from BlockComparator)
    if (isDiffContainer && diffs) {
        return (
            <span className={className}>
                {diffs.map((part, idx) => {
                    let wordClass = 'diff-word';
                    if (part.added) wordClass += ' diff-word-added';
                    if (part.removed) wordClass += ' diff-word-removed';
                    return <span key={idx} className={wordClass}>{part.value}</span>;
                })}
            </span>
        );
    }

    // 3. Document/Container Nodes
    if (type === 'doc') {
        return (
            <div className="diff-doc">
                {content?.map((child, i) => (
                    <DiffNodeRenderer key={i} node={child} />
                ))}
            </div>
        );
    }

    // 4. Tables
    if (type === 'table') {
        return (
            <table className={className}>
                <tbody>
                    {content?.map((child, i) => <DiffNodeRenderer key={i} node={child} />)}
                </tbody>
            </table>
        );
    }
    if (type === 'tableRow') {
        return (
            <tr className={className}>
                {content?.map((child, i) => <DiffNodeRenderer key={i} node={child} />)}
            </tr>
        );
    }
    if (type === 'tableCell' || type === 'tableHeader') {
        const Tag = type === 'tableHeader' ? 'th' : 'td';
        return (
            <Tag className={className} colSpan={attrs?.colspan} rowSpan={attrs?.rowspan}>
                {content?.map((child, i) => <DiffNodeRenderer key={i} node={child} />)}
            </Tag>
        );
    }

    // 5. Standard Blocks (Paragraphs, Headings, Lists)
    const renderChildren = () => content?.map((child, i) => <DiffNodeRenderer key={i} node={child} />);

    switch (type) {
        case 'paragraph':
            return <p className={className}>{renderChildren()}</p>;
        case 'heading':
            const Tag = `h${attrs.level || 1}`;
            return <Tag className={className}>{renderChildren()}</Tag>;
        case 'bulletList':
            return <ul className={className}>{renderChildren()}</ul>;
        case 'orderedList':
            return <ol className={className}>{renderChildren()}</ol>;
        case 'listItem':
            return <li className={className}>{renderChildren()}</li>;
        case 'blockquote':
            return <blockquote className={className}>{renderChildren()}</blockquote>;
        default:
            return <div className={className}>{renderChildren()}</div>;
    }
};

const SideBySideViewer = ({ oldVersion, newVersion, onClose }) => {
    // Generate the specialized AST highlighting differences
    const diffAst = useMemo(() => {
        if (!oldVersion || !newVersion) return null;
        return generateDocumentDiff(oldVersion.json, newVersion.json);
    }, [oldVersion, newVersion]);

    if (!oldVersion || !newVersion) {
        return <div className="sbs-error">Missing versions for comparison.</div>;
    }

    return (
        <div className="sbs-overlay">
            <div className="sbs-modal">
                <div className="sbs-header">
                    <h2>
                        Comparing <span className="sbs-badge old">{oldVersion.id}</span>
                        {' vs '}
                        <span className="sbs-badge new">{newVersion.id}</span>
                    </h2>
                    <button className="sbs-close" onClick={onClose}>&times;</button>
                </div>

                <div className="sbs-body">
                    {/* Left Panel: Old Version rendering exactly as it was */}
                    <div className="sbs-panel sbs-old-panel">
                        <div className="sbs-panel-title">Original ({oldVersion.id})</div>
                        <div className="sbs-content tiptap read-only">
                            <DiffNodeRenderer node={oldVersion.json} />
                        </div>
                    </div>

                    {/* Right Panel: New Version heavily annotated with diffs */}
                    <div className="sbs-panel sbs-diff-panel">
                        <div className="sbs-panel-title">Changes ({newVersion.id})</div>
                        <div className="sbs-content tiptap read-only">
                            {diffAst && <DiffNodeRenderer node={diffAst} />}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SideBySideViewer;
