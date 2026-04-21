/**
 * SOPConfigContext.jsx
 *
 * React context provider for SOP workflow configuration.
 *
 * Phase 1 (now):  Serves the static default config from sopWorkflowConfig.js
 * Phase 2 (later): Fetches config from backend API and merges with defaults
 *
 * Usage:
 *   Wrap your app:   <SOPConfigProvider> ... </SOPConfigProvider>
 *   In components:   const config = useSOPConfig()
 */
import { createContext, useContext, useState } from 'react'
import defaultConfig, { mergeConfig } from '../utils/sopWorkflowConfig'

const SOPConfigContext = createContext(null)

/**
 * Provider component — place this in main.jsx or App.jsx.
 *
 * @param {Object} props
 * @param {Object} [props.overrides] - Optional partial config to merge over defaults
 * @param {React.ReactNode} props.children
 */
export function SOPConfigProvider({ children, overrides = null }) {
    const [config] = useState(() => mergeConfig(defaultConfig, overrides))

    // Phase 2: uncomment to load config from backend API
    // useEffect(() => {
    //   fetch('/api/sop-workflow-config')
    //     .then(res => res.json())
    //     .then(remote => setConfig(mergeConfig(defaultConfig, remote)))
    //     .catch(() => { /* keep default config on error */ })
    // }, [])

    return (
        <SOPConfigContext.Provider value={config}>
            {children}
        </SOPConfigContext.Provider>
    )
}

/**
 * Hook to access SOP workflow config from any component.
 * Falls back to the static default if used outside the provider.
 */
export function useSOPConfig() {
    const ctx = useContext(SOPConfigContext)
    return ctx || defaultConfig
}
