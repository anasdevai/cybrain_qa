export default function VersionSidebar({
    versions = [],
    currentVersion,
    onLoadVersion,
}) {
    return (
        <div className="contract-panel">
            <div className="contract-panel-header">
                <h3>Versions</h3>
            </div>

            <div className="version-list">
                {versions.length === 0 ? (
                    <p className="muted-text">No versions available.</p>
                ) : (
                    versions.map((version) => {
                        const versionId = version.id || version.versionId || version.name
                        const label = version.label || versionId

                        return (
                            <button
                                key={versionId}
                                type="button"
                                onClick={() => onLoadVersion(versionId)}
                                className={`version-item ${currentVersion === versionId ? 'active' : ''
                                    }`}
                            >
                                <span className="version-title">{label}</span>
                            </button>
                        )
                    })
                )}
            </div>
        </div>
    )
}