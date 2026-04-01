import { useState } from 'react'
import { useLanguage } from '../../context/LanguageContext'

export default function SOPReferencesPanel({
    references = [],
    onChange,
    isReadOnly = false,
}) {
    const { t } = useLanguage()
    const [value, setValue] = useState('')

    const addReference = () => {
        const trimmed = value.trim()
        if (!trimmed) return

        onChange?.([...references, trimmed])
        setValue('')
    }

    const removeReference = (indexToRemove) => {
        onChange?.(references.filter((_, index) => index !== indexToRemove))
    }

    const validReferences = Array.isArray(references) ? references : []

    return (
        <div className="contract-panel">
            <h3>{t.sopReferences}</h3>

            {!isReadOnly && (
                <div className="review-link-box" style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        placeholder={t.addReference}
                        className="review-link-input"
                    />
                    <button type="button" className="primary-btn sop-add-btn" onClick={addReference}>
                        {t.add}
                    </button>
                </div>
            )}

            {validReferences.length === 0 ? (
                <p className="muted-text">{t.noReferencesYet}</p>
            ) : (
                <div className="review-comments-list">
                    {validReferences.map((ref, index) => (
                        <div
                            key={`${ref}-${index}`}
                            className="review-comment-item"
                        >
                            <div className="variable-label-row">
                                <span style={{ wordBreak: 'break-word', minWidth: 0 }}>{ref}</span>
                                {!isReadOnly && (
                                    <button
                                        type="button"
                                        className="danger-btn"
                                        onClick={() => removeReference(index)}
                                    >
                                        {t.remove}
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}