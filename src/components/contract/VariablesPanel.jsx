/**
 * VariablesPanel.jsx
 * 
 * Renders a sidebar panel displaying a list of all detected placeholder variables
 * within the document. Allows the user to input values to resolve these placeholders
 * and track which variables are still 'missing'.
 */
import { useLanguage } from '../../context/LanguageContext'

/**
 * VariablesPanel Component
 * 
 * @param {Object} props
 * @param {Array} props.variableEntries - Structured array of variables (name, value, status).
 * @param {Function} props.onChange - Callback fired when a variable input changes.
 * @param {Function} props.onReset - Callback to clear all variable values.
 */
export default function VariablesPanel({
    variableEntries = [],
    onChange,
    onReset,
}) {
    const { t } = useLanguage()

    return (
        <div className="contract-panel">
            <div className="contract-panel-header">
                <h3>{t.variables}</h3>

                {onReset && (
                    <button
                        type="button"
                        onClick={onReset}
                        className="secondary-btn"
                    >
                        {t.reset}
                    </button>
                )}
            </div>

            <div className="variables-list">
                {variableEntries.length === 0 ? (
                    <p className="muted-text">{t.noVariablesFound}</p>
                ) : (
                    variableEntries.map((item) => (
                        <div key={item.name} className="variable-field">
                            <div className="variable-label-row">
                                <label htmlFor={item.name}>{item.name}</label>

                                <span
                                    className={
                                        item.status === 'Resolved'
                                            ? 'status-text resolved'
                                            : 'status-text missing'
                                    }
                                >
                                    {item.status === 'Resolved' ? t.resolved : t.missing}
                                </span>
                            </div>

                            <input
                                id={item.name}
                                type="text"
                                value={item.value}
                                placeholder={item.name}
                                onChange={(e) => onChange(item.name, e.target.value)}
                            />
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}