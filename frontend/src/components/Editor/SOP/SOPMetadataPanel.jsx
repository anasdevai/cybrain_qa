import { Settings } from 'lucide-react'
import { useLanguage } from '../../../context/LanguageContext'
import { useSOPConfig } from '../../../context/SOPConfigContext'

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
        const { key, type, label, multiValue, separator } = fieldDef
        const hasError = errors[key]
        const displayLabel = t[label] || label

        let inputElement = null

        // Multi-value textarea (e.g. regulatoryReferences)
        if (type === 'textarea' && multiValue) {
            const arrayValue = Array.isArray(metadata?.[key]) ? metadata[key] : []
            inputElement = (
                <textarea
                    placeholder={displayLabel}
                    className="sop-textarea"
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
            )
        } else if (type === 'textarea') {
            // Regular textarea
            inputElement = (
                <textarea
                    placeholder={displayLabel}
                    className="sop-textarea"
                    value={metadata?.[key] || ''}
                    onChange={(e) => handleFieldChange(key, e.target.value)}
                    disabled={isReadOnly}
                    rows={4}
                />
            )
        } else if (type === 'date') {
            // Date input
            inputElement = (
                <input
                    type="date"
                    className="sop-input"
                    value={metadata?.[key] || ''}
                    onChange={(e) => handleFieldChange(key, e.target.value)}
                    disabled={isReadOnly}
                />
            )
        } else {
            // Default: text input
            inputElement = (
                <input
                    type="text"
                    className="sop-input"
                    placeholder={displayLabel}
                    value={metadata?.[key] || ''}
                    onChange={(e) => handleFieldChange(key, e.target.value)}
                    disabled={isReadOnly}
                />
            )
        }

        return (
            <div key={key} className="sop-field-group">
                <label className="sop-field-label">{displayLabel}</label>
                {inputElement}
                {hasError && (
                    <p className="error-text">{hasError}</p>
                )}
            </div>
        )
    }

    return (
        <div className="sop-panel-card">
            <h3 className="sop-panel-title">
                <Settings size={18} />
                {t.sopMetadata}
            </h3>

            <div className="sop-metadata-grid">
                {config.metadataFields.map(renderField)}
            </div>
        </div>
    )
}

