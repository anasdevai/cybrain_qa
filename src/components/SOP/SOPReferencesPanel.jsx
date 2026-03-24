import { useState } from 'react'

export default function SOPReferencesPanel({
    references = [],
    onChange,
    isReadOnly = false,
}) {
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

    return (
        <div className="review-actions">
            <h3>SOP References</h3>

            {!isReadOnly && (
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        placeholder="Add reference / citation"
                        style={{ flex: 1 }}
                    />
                    <button type="button" className="primary-btn" onClick={addReference}>
                        Add
                    </button>
                </div>
            )}

            {references.length === 0 ? (
                <p className="muted-text">No references added yet.</p>
            ) : (
                <div style={{ display: 'grid', gap: 8 }}>
                    {references.map((ref, index) => (
                        <div
                            key={`${ref}-${index}`}
                            style={{
                                border: '1px solid #d1d5db',
                                borderRadius: 10,
                                padding: '10px 12px',
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                                <span>{ref}</span>
                                {!isReadOnly && (
                                    <button
                                        type="button"
                                        className="danger-btn"
                                        onClick={() => removeReference(index)}
                                    >
                                        Remove
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