import { useState } from 'react'
import { Bookmark, Plus, Trash2 } from 'lucide-react'
import { useLanguage } from '../../../context/LanguageContext'

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
        <div className="sop-panel-card">
            <h3 className="sop-panel-title">
                <Bookmark size={18} />
                {t.sopReferences}
            </h3>

            {!isReadOnly && (
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        placeholder={t.addReference}
                        className="sop-input"
                    />
                    <button 
                        type="button" 
                        className="sop-action-btn primary" 
                        onClick={addReference}
                        style={{ padding: '0 12px', minHeight: 40 }}
                    >
                        <Plus size={18} />
                    </button>
                </div>
            )}

            {validReferences.length === 0 ? (
                <p className="muted-text">{t.noReferencesYet}</p>
            ) : (
                <div className="sop-metadata-grid">
                    {validReferences.map((ref, index) => (
                        <div
                            key={`${ref}-${index}`}
                            className="sop-status-row"
                            style={{ margin: 0, padding: '10px 14px', background: '#f9fcfb' }}
                        >
                            <span style={{ fontSize: 13, wordBreak: 'break-word', color: '#374151', flex: 1 }}>{ref}</span>
                            {!isReadOnly && (
                                <button
                                    type="button"
                                    onClick={() => removeReference(index)}
                                    style={{ 
                                        background: 'transparent', 
                                        border: 'none', 
                                        color: '#ef4444', 
                                        cursor: 'pointer',
                                        padding: 4,
                                        display: 'flex',
                                        alignItems: 'center'
                                    }}
                                >
                                    <Trash2 size={14} />
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

