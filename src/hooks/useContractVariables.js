/**
 * useContractVariables.js
 * 
 * A custom React hook designed to manage and track dynamic variables
 * extracted from placeholders within the document text.
 */
import { useCallback, useMemo, useState } from 'react'
import { CONTRACT_DEFAULT_VARIABLES } from '../utils/contractConstants'
import { buildVariablesObject } from '../utils/resolveVariables'

/**
 * Hook to manage contract variables mapped to document placeholders.
 * @param {Object} initialVariables - The initial set of variables to hydrate into state.
 * @returns {Object} Methods and state properties for interacting with document variables.
 */
export default function useContractVariables(initialVariables = CONTRACT_DEFAULT_VARIABLES) {
    const [variables, setVariables] = useState(initialVariables)

    /**
     * Updates a single variable's value dynamically based on its key.
     * Overrides only the requested key, keeping others intact.
     */
    const updateVariable = useCallback((key, value) => {
        setVariables((prev) => {
            if (prev[key] === value) return prev
            return {
                ...prev,
                [key]: value,
            }
        })
    }, [])

    /**
     * Updates multiple variable values dynamically at once.
     */
    const updateMultipleVariables = useCallback((newValues) => {
        setVariables((prev) => {
            const next = {
                ...prev,
                ...newValues,
            }

            const prevStr = JSON.stringify(prev)
            const nextStr = JSON.stringify(next)

            if (prevStr === nextStr) return prev
            return next
        })
    }, [])

    /**
     * Completely formats/wipes out the active variables list.
     */
    const resetVariables = useCallback(() => {
        setVariables({})
    }, [])

    /**
     * Parses the current document state placeholders and ensures they are mapped in the variables object.
     * Prevents redundant rerenders via string comparison.
     */
    const syncPlaceholders = useCallback((placeholderNames = []) => {
        setVariables((prev) => {
            const next = buildVariablesObject(placeholderNames, prev)

            const prevStr = JSON.stringify(prev)
            const nextStr = JSON.stringify(next)

            if (prevStr === nextStr) return prev
            return next
        })
    }, [])

    /**
     * Extrapolates detailed objects containing properties like 'status' and 'name'
     * for easy rendering down into standard components.
     */
    const variableEntries = useMemo(() => {
        return Object.entries(variables).map(([name, value]) => ({
            name,
            value,
            // A variable is 'Missing' if it doesn't contain a valid value/string, otherwise 'Resolved'
            status: value?.toString().trim() ? 'Resolved' : 'Missing',
        }))
    }, [variables])

    // Convenience computed property for filtering missing variables
    const missingVariables = useMemo(() => {
        return variableEntries.filter((item) => item.status === 'Missing')
    }, [variableEntries])

    // Convenience computed property for filtering completely populated variables
    const resolvedVariables = useMemo(() => {
        return variableEntries.filter((item) => item.status === 'Resolved')
    }, [variableEntries])

    // Helper flag determining if all variables required by the document are resolved
    const allResolved = variableEntries.length > 0 && missingVariables.length === 0

    return {
        variables,
        setVariables,
        updateVariable,
        updateMultipleVariables,
        resetVariables,
        syncPlaceholders,
        variableEntries, // Array of variables structured for UI consumption
        missingVariables,
        resolvedVariables,
        allResolved,
    }
}