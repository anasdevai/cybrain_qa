export default function SOPMetadataPanel({
    metadata,
    onChange,
    isReadOnly = false,
}) {
    const handleFieldChange = (field, value) => {
        onChange?.({
            ...metadata,
            [field]: value,
        })
    }

    return (
        <div className="review-actions">
            <h3>SOP Metadata</h3>

            <div style={{ display: 'grid', gap: 10 }}>
                <input
                    type="text"
                    placeholder="Document ID"
                    value={metadata?.documentId || ''}
                    onChange={(e) => handleFieldChange('documentId', e.target.value)}
                    disabled={isReadOnly}
                />

                <input
                    type="text"
                    placeholder="Department"
                    value={metadata?.department || ''}
                    onChange={(e) => handleFieldChange('department', e.target.value)}
                    disabled={isReadOnly}
                />

                <input
                    type="text"
                    placeholder="Author"
                    value={metadata?.author || ''}
                    onChange={(e) => handleFieldChange('author', e.target.value)}
                    disabled={isReadOnly}
                />

                <input
                    type="text"
                    placeholder="Reviewer"
                    value={metadata?.reviewer || ''}
                    onChange={(e) => handleFieldChange('reviewer', e.target.value)}
                    disabled={isReadOnly}
                />

                <input
                    type="date"
                    value={metadata?.effectiveDate || ''}
                    onChange={(e) => handleFieldChange('effectiveDate', e.target.value)}
                    disabled={isReadOnly}
                />

                <input
                    type="date"
                    value={metadata?.reviewDate || ''}
                    onChange={(e) => handleFieldChange('reviewDate', e.target.value)}
                    disabled={isReadOnly}
                />

                <input
                    type="text"
                    placeholder="Risk Level"
                    value={metadata?.riskLevel || ''}
                    onChange={(e) => handleFieldChange('riskLevel', e.target.value)}
                    disabled={isReadOnly}
                />
            </div>
        </div>
    )
}