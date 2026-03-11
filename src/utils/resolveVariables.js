export const extractPlaceholdersFromText = (text = '') => {
    const matches = [...text.matchAll(/\{\{([A-Za-z0-9_]+)\}\}/g)]
    const unique = [...new Set(matches.map(match => match[1]))]
    return unique
}

export const buildVariablesObject = (placeholderNames = [], existingValues = {}) => {
    return placeholderNames.reduce((acc, name) => {
        acc[name] = existingValues[name] || ''
        return acc
    }, {})
}

export const resolveTextWithVariables = (text = '', variables = {}) => {
    return text.replace(/\{\{([A-Za-z0-9_]+)\}\}/g, (_, name) => {
        const value = variables[name]
        return value && value.toString().trim() ? value : `{{${name}}}`
    })
}