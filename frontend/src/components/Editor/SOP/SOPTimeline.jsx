import { useLanguage } from '../../../context/LanguageContext'
import { useSOPConfig } from '../../../context/SOPConfigContext'

export default function SOPTimeline({ sopStatus }) {
  const { t } = useLanguage()
  const config = useSOPConfig()

  return (
    <div className="sop-panel">
      <h3>{t.sopLifecycle}</h3>
      <div className="sop-lifecycle-list">
        {config.states.map((state) => {
          const isActive = state.id === sopStatus
          const displayLabel = t[state.label] || state.label

          return (
            <div
              key={state.id}
              className={`sop-lifecycle-item${isActive ? ' is-active' : ''}`}
            >
              <span className="sop-lifecycle-text">{displayLabel}</span>
              {isActive ? <span className="sop-lifecycle-badge">{t.current}</span> : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}
