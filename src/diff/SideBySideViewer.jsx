import React, { useMemo } from 'react';
import { generateDocumentDiff } from './VersionDiffEngine';
import './SideBySideViewer.css';

const applyMarks = (node, children) => {
    const marks = node?.marks || [];
    if (!marks.length) return children;

    return marks.reduce((acc, mark, index) => {
        switch (mark.type) {
            case 'bold':
                return <strong key={index}>{acc}</strong>;
            case 'italic':
                return <em key={index}>{acc}</em>;
            case 'underline':
                return <u key={index}>{acc}</u>;
            case 'strike':
                return <s key={index}>{acc}</s>;
            case 'link':
                return (
                    <a
                        key={index}
                        href={mark.attrs?.href || '#'}
                        target="_blank"
                        rel="noreferrer"
                    >
                        {acc}
                    </a>
                );
            default:
                return acc;
        }
    }, children);
};

// A recursive renderer that walks the specialized diff AST
const DiffNodeRenderer = ({ node }) => {
    if (!node) return null;

    const { type, text, attrs, content, diffStatus, isDiffContainer, diffs } = node;

    let className = 'diff-node';
    if (diffStatus === 'added') className += ' diff-added';
    if (diffStatus === 'removed') className += ' diff-removed';

    // TEXT NODE
    if (type === 'text') {
        const rendered = <span className={className}>{text}</span>;
        return applyMarks(node, rendered);
    }

    // DIFF CONTAINER
    if (isDiffContainer && diffs) {
        const renderDiffContent = () =>
            diffs.map((part, idx) => {
                let wordClass = 'diff-word';
                if (part.added) wordClass += ' diff-word-added';
                if (part.removed) wordClass += ' diff-word-removed';

                const needsSpace =
                    idx < diffs.length - 1 &&
                    !String(part.value || '').endsWith(' ') &&
                    !String(diffs[idx + 1]?.value || '').startsWith(' ');

                const wordNode = (
                    <React.Fragment key={idx}>
                        <span className={wordClass}>
                            {part.value}
                        </span>
                        {needsSpace ? <span>{'\u00A0\u00A0'}</span> : null}
                    </React.Fragment>
                );

                return part.marks?.length ? applyMarks(part, wordNode) : wordNode;
            });

        switch (type) {
            case 'paragraph':
                return <p className={className}>{renderDiffContent()}</p>;

            case 'heading':
                return React.createElement(
                    `h${attrs?.level || 1}`,
                    { className },
                    renderDiffContent()
                );

            case 'listItem':
                return <li className={className}>{renderDiffContent()}</li>;

            case 'bulletList':
                return (
                    <ul className={className}>
                        <li>{renderDiffContent()}</li>
                    </ul>
                );

            case 'orderedList':
                return (
                    <ol className={className}>
                        <li>{renderDiffContent()}</li>
                    </ol>
                );

            default:
                return <div className={className}>{renderDiffContent()}</div>;
        }
    }

    // DOCUMENT
    if (type === 'doc') {
        return (
            <div className="diff-doc">
                {content?.map((child, i) => (
                    <DiffNodeRenderer key={i} node={child} />
                ))}
            </div>
        );
    }

    // TABLES
    if (type === 'table') {
        return (
            <table className={className}>
                <tbody>
                    {content?.map((child, i) => (
                        <DiffNodeRenderer key={i} node={child} />
                    ))}
                </tbody>
            </table>
        );
    }

    if (type === 'tableRow') {
        return (
            <tr className={className}>
                {content?.map((child, i) => (
                    <DiffNodeRenderer key={i} node={child} />
                ))}
            </tr>
        );
    }

    if (type === 'tableCell' || type === 'tableHeader') {
        const Tag = type === 'tableHeader' ? 'th' : 'td';
        return (
            <Tag className={className} colSpan={attrs?.colspan} rowSpan={attrs?.rowspan}>
                {content?.map((child, i) => (
                    <DiffNodeRenderer key={i} node={child} />
                ))}
            </Tag>
        );
    }

    const renderChildren = () =>
        content?.map((child, i) => <DiffNodeRenderer key={i} node={child} />);

    switch (type) {
        case 'paragraph':
            return <p className={className}>{renderChildren()}</p>;

        case 'heading': {
            const Tag = `h${attrs?.level || 1}`;
            return <Tag className={className}>{renderChildren()}</Tag>;
        }

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
                    <div className="sbs-panel sbs-old-panel">
                        <div className="sbs-panel-title">Original ({oldVersion.id})</div>
                        <div className="sbs-content read-only">
                            {oldVersion.json ? (
                                <DiffNodeRenderer node={oldVersion.json} />
                            ) : (
                                <p>No content in original version.</p>
                            )}
                        </div>
                    </div>

                    <div className="sbs-panel sbs-diff-panel">
                        <div className="sbs-panel-title">Changes ({newVersion.id})</div>
                        <div className="sbs-content read-only">
                            {diffAst && diffAst.content?.length > 0 ? (
                                <DiffNodeRenderer node={diffAst} />
                            ) : (
                                <p className="no-changes">No changes detected between these versions.</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SideBySideViewer;