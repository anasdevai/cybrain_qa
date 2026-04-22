/**
 * SOPMetadataPanel.jsx
 *
 * Config-driven SOP metadata form.
 *
 * Before: 10 hardcoded input fields.
 * After:  reads config.metadataFields[] to render fields dynamically.
 *         Adding a new metadata field = adding one entry to config.
 */
import { useLanguage } from '../../context/LanguageContext'
import { useSOPConfig } from '../../context/SOPConfigContext'

export default function SOPMetadataPanel({
    metadata,
    onChange,
    isReadOnly = false,
    errors = {},
}) {
    const { t } = useLanguage()
    const config = useSOPConfig()

    const handleFieldChange = (key, value) => {
        onChange?.({
            ...metadata,
            [key]: value,
        })
    }

    /**
     * Render a single metadata field based on its config definition.
     */
    const renderField = (fieldDef) => {
        const { key, type, label, required, multiValue, separator } = fieldDef
        const hasError = errors[key]

        // Multi-value textarea (e.g. regulatoryReferences)
        if (type === 'textarea' && multiValue) {
            const arrayValue = Array.isArray(metadata?.[key]) ? metadata[key] : []
            return (
                <div key={key}>
                    <textarea
                        placeholder={t[label] || label}
                        value={arrayValue.join(separator || '\n')}
                        onChange={(e) =>
                            handleFieldChange(
                                key,
                                e.target.value
                                    .split(separator || '\n')
                                    .map((item) => item.trim())
                                    .filter(Boolean)
                            )
                        }
                        disabled={isReadOnly}
                        rows={4}
                    />
                    {hasError && (
                        <p style={{ color: 'red', fontSize: 12 }}>{hasError}</p>
                    )}
                </div>
            )
        }

        // Regular textarea
        if (type === 'textarea') {
            return (
                <div key={key}>
                    <textarea
                        placeholder={t[label] || label}
                        value={metadata?.[key] || ''}
                        onChange={(e) => handleFieldChange(key, e.target.value)}
                        disabled={isReadOnly}
                        rows={4}
                    />
                    {hasError && (
                        <p style={{ color: 'red', fontSize: 12 }}>{hasError}</p>
                    )}
                </div>
            )
        }

        // Date input
        if (type === 'date') {
            return (
                <div key={key}>
                    <input
                        type="date"
                        value={metadata?.[key] || ''}
                        onChange={(e) => handleFieldChange(key, e.target.value)}
                        disabled={isReadOnly}
                        title={t[label] || label}
                    />
                    {hasError && (
                        <p style={{ color: 'red', fontSize: 12 }}>{hasError}</p>
                    )}
                </div>
            )
        }

        // Default: text input
        return (
            <div key={key}>
                <input
                    type="text"
                    placeholder={t[label] || label}
                    value={metadata?.[key] || ''}
                    onChange={(e) => handleFieldChange(key, e.target.value)}
                    disabled={isReadOnly}
                />
                {hasError && (
                    <p style={{ color: 'red', fontSize: 12 }}>{hasError}</p>
                )}
            </div>
        )
    }

    return (
        <div className="review-actions">
            <h3>{t.sopMetadata}</h3>

            <div style={{ display: 'grid', gap: 10 }}>
                {config.metadataFields.map(renderField)}
            </div>
        </div>
    )
}