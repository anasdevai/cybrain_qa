import { useCallback, useMemo, useState } from 'react'
import { CONTRACT_DEFAULT_VARIABLES } from '../utils/contractConstants'
import { buildVariablesObject } from '../utils/resolveVariables'

export default function useContractVariables(initialVariables = CONTRACT_DEFAULT_VARIABLES) {
    const [variables, setVariables] = useState(initialVariables)

    const updateVariable = useCallback((key, value) => {
        setVariables((prev) => {
            if (prev[key] === value) return prev
            return {
                ...prev,
                [key]: value,
            }
        })
    }, [])

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

    const resetVariables = useCallback(() => {
        setVariables({})
    }, [])

    const syncPlaceholders = useCallback((placeholderNames = []) => {
        setVariables((prev) => {
            const next = buildVariablesObject(placeholderNames, prev)

            const prevStr = JSON.stringify(prev)
            const nextStr = JSON.stringify(next)

            if (prevStr === nextStr) return prev
            return next
        })
    }, [])

    const variableEntries = useMemo(() => {
        return Object.entries(variables).map(([name, value]) => ({
            name,
            value,
            status: value?.toString().trim() ? 'Resolved' : 'Missing',
        }))
    }, [variables])

    const missingVariables = useMemo(() => {
        return variableEntries.filter((item) => item.status === 'Missing')
    }, [variableEntries])

    const resolvedVariables = useMemo(() => {
        return variableEntries.filter((item) => item.status === 'Resolved')
    }, [variableEntries])

    const allResolved = variableEntries.length > 0 && missingVariables.length === 0

    return {
        variables,
        setVariables,
        updateVariable,
        updateMultipleVariables,
        resetVariables,
        syncPlaceholders,
        variableEntries,
        missingVariables,
        resolvedVariables,
        allResolved,
    }
}