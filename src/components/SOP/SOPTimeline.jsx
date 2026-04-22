/**
 * SOPTimeline.jsx
 *
 * Config-driven SOP lifecycle timeline.
 *
 * Before: hardcoded SOP_ORDER array with 4 fixed states.
 * After:  reads config.states[] to render any number of lifecycle steps.
 */
import { useLanguage } from '../../context/LanguageContext'
import { useSOPConfig } from '../../context/SOPConfigContext'

export default function SOPTimeline({ sopStatus }) {
    const { t } = useLanguage()
    const config = useSOPConfig()

    const stateIds = config.states.map((s) => s.id)
    const currentIndex = stateIds.indexOf(sopStatus)

    return (
        <div className="contract-panel">
            <h3>{t.sopLifecycle}</h3>

            <div className="workflow-list">
                {config.states.map((state, index) => {
                    const isActive = state.id === sopStatus
                    const isCompleted = currentIndex >= index && currentIndex !== -1

                    return (
                        <div
                            key={state.id}
                            className={`timeline-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                            style={{
                                padding: '10px 12px',
                                borderRadius: 10,
                                border: '1px solid #d1d5db',
                                background: isActive ? '#eef2ff' : '#fff',
                            }}
                        >
                            <strong>{t[state.label] || state.label}</strong>
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