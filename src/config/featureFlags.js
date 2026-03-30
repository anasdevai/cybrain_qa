/**
 * featureFlags.js
 *
 * Centralized feature flag configuration for the AI-LAW Editor.
 * Toggle profiles on/off here without touching component code.
 *
 * To re-enable the Contract profile later, simply set
 * contractProfileEnabled back to true.
 */

const featureFlags = {
  /** Enable or disable the Contract profile across the entire app */
  contractProfileEnabled: false,

  /** Enable or disable the SOP profile across the entire app */
  sopProfileEnabled: true,

  /** The default profile to use when the app loads or when an invalid profile is detected */
  defaultProfile: 'sop',
}

export default featureFlags
