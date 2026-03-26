import { useLanguage } from '../../context/LanguageContext'

export default function SOPMetadataPanel({
    metadata,
    onChange,
    isReadOnly = false,
    errors = {},
}) {
    const { t } = useLanguage()

    const handleFieldChange = (field, value) => {
        onChange?.({
            ...metadata,
            [field]: value,
        })
    }

    return (
        <div className="contract-panel">
            <h3>{t.sopMetadata}</h3>

            <div className="variables-list">
                <div>
                    <input
                        type="text"
                        placeholder={t.documentId}
                        value={metadata?.documentId || ''}
                        onChange={(e) => handleFieldChange('documentId', e.target.value)}
                        disabled={isReadOnly}
                    />
                    {errors.documentId && (
                        <p style={{ color: 'red', fontSize: 12 }}>{errors.documentId}</p>
                    )}
                </div>

                <div>
                    <input
                        type="text"
                        placeholder={t.department}
                        value={metadata?.department || ''}
                        onChange={(e) => handleFieldChange('department', e.target.value)}
                        disabled={isReadOnly}
                    />
                </div>

                <div>
                    <input
                        type="text"
                        placeholder={t.author}
                        value={metadata?.author || ''}
                        onChange={(e) => handleFieldChange('author', e.target.value)}
                        disabled={isReadOnly}
                    />
                    {errors.author && (
                        <p style={{ color: 'red', fontSize: 12 }}>{errors.author}</p>
                    )}
                </div>

                <div>
                    <input
                        type="text"
                        placeholder={t.reviewer}
                        value={metadata?.reviewer || ''}
                        onChange={(e) => handleFieldChange('reviewer', e.target.value)}
                        disabled={isReadOnly}
                    />
                    {errors.reviewer && (
                        <p style={{ color: 'red', fontSize: 12 }}>{errors.reviewer}</p>
                    )}
                </div>

                <input
                    type="date"
                    value={metadata?.effectiveDate || ''}
                    onChange={(e) => handleFieldChange('effectiveDate', e.target.value)}
                    disabled={isReadOnly}
                    title={t.effectiveDate}
                />

                <input
                    type="date"
                    value={metadata?.reviewDate || ''}
                    onChange={(e) => handleFieldChange('reviewDate', e.target.value)}
                    disabled={isReadOnly}
                    title={t.reviewDate}
                />

                <input
                    type="text"
                    placeholder={t.riskLevel}
                    value={metadata?.riskLevel || ''}
                    onChange={(e) => handleFieldChange('riskLevel', e.target.value)}
                    disabled={isReadOnly}
                />
            </div>
        </div>
    )
}