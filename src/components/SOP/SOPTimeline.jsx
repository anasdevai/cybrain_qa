import { SOP_LABELS, SOP_ORDER } from '../../utils/sopConstants'

export default function SOPTimeline({ sopStatus }) {
    const currentIndex = SOP_ORDER.indexOf(sopStatus)

    return (
        <div className="workflow-timeline">
            <h3>SOP Lifecycle</h3>

            <div style={{ display: 'grid', gap: 10 }}>
                {SOP_ORDER.map((step, index) => {
                    const isActive = step === sopStatus
                    const isCompleted = currentIndex >= index && currentIndex !== -1

                    return (
                        <div
                            key={step}
                            className={`timeline-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                            style={{
                                padding: '10px 12px',
                                borderRadius: 10,
                                border: '1px solid #d1d5db',
                                background: isActive ? '#eef2ff' : '#fff',
                            }}
                        >
                            <strong>{SOP_LABELS[step] || step}</strong>
                            {isActive && (
                                <span style={{ marginLeft: 8, fontSize: 12 }}>
                                    (Current)
                                </span>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}