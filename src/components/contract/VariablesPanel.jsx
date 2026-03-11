export default function VariablesPanel({
    variableEntries = [],
    onChange,
    onReset,
}) {
    return (
        <div className="contract-panel">
            <div className="contract-panel-header">
                <h3>Variables</h3>
                <button type="button" onClick={onReset} className="secondary-btn">
                    Reset
                </button>
            </div>

            <div className="variables-list">
                {variableEntries.map((item) => (
                    <div key={item.name} className="variable-field">
                        <div className="variable-label-row">
                            <label htmlFor={item.name}>{item.name}</label>
                            <span className={`status-text ${item.status === 'Resolved' ? 'resolved' : 'missing'}`}>
                                {item.status}
                            </span>
                        </div>

                        <input
                            id={item.name}
                            type="text"
                            value={item.value}
                            placeholder={`Enter ${item.name}`}
                            onChange={(e) => onChange(item.name, e.target.value)}
                        />
                    </div>
                ))}
            </div>
        </div>
    )
}