import { useLanguage } from '../../context/LanguageContext'
import { SOP_ORDER } from '../../utils/sopConstants'

export default function SOPTimeline({ sopStatus }) {
    const { t } = useLanguage()

    const labelMap = {
        draft: t.draft,
        under_review: t.underReview,
        effective: t.effective,
        obsolete: t.obsolete,
    }

    const currentIndex = SOP_ORDER.indexOf(sopStatus)

    return (
        <div className="contract-panel">
            <h3>{t.sopLifecycle}</h3>

            <div className="workflow-list">
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
                            <strong>{labelMap[step] || step}</strong>
                            {isActive && (
                                <span style={{ marginLeft: 8, fontSize: 12 }}>
                                    ({t.current})
                                </span>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}