/**
 * resolveVariables.js
 * 
 * Utility functions for extracting, building, and resolving placeholder variables
 * within text content. Variable placeholders match the pattern {{variableName}}.
 */

// Regular expression to match variables encapsulated by double curly braces.
export const PLACEHOLDER_REGEX = /\{\{([A-Za-z0-9_]+)\}\}/g;

/**
 * Extracts a unique list of placeholder names from a given text string.
 * @param {string} text - The input text to search for variables.
 * @returns {Array<string>} An array of unique variable names identified in the text.
 */
export const extractPlaceholdersFromText = (text = "") => {
    // Collect all matches
    const matches = [...text.matchAll(PLACEHOLDER_REGEX)];
    // Deduplicate the extracted names (e.g., matching "name" inside "{{name}}")
    const unique = [...new Set(matches.map((match) => match[1]))];
    return unique;
};

/**
 * Creates a map of placeholder names to their respective values, 
 * retaining existing values if present or initializing them as empty strings.
 * @param {Array<string>} placeholderNames - The list of placeholder variable names.
 * @param {Object} existingValues - Current map of variable values.
 * @returns {Object} A fresh variable mapping object.
 */
export const buildVariablesObject = (placeholderNames = [], existingValues = {}) => {
    return placeholderNames.reduce((acc, name) => {
        // Carry over the existing value, otherwise fallback to an empty string
        acc[name] = existingValues[name] ?? "";
        return acc;
    }, {});
};

/**
 * Replaces placeholders in a given string with their corresponding values
 * from the variables object. If a variable is missing or empty, the placeholder
 * is kept unchanged.
 * @param {string} text - The template text containing {{variables}}.
 * @param {Object} variables - Dictionary containing variable key-value pairs.
 * @returns {string} The formatted text with placeholders resolved.
 */
export const resolveTextWithVariables = (text = "", variables = {}) => {
    return text.replace(PLACEHOLDER_REGEX, (_, name) => {
        const value = variables[name];

        // If no value exists in the dictionary, leave the placeholder intact
        if (value === null || value === undefined) {
            return `{{${name}}}`;
        }

        const stringValue = String(value).trim();

        // If the variable is merely whitespace or empty, keep the placeholder visible
        return stringValue ? stringValue : `{{${name}}}`;
    });
};