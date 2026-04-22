/**
 * LanguageContext.jsx
 * 
 * Provides global localization (i18n) state management mapped to `translations.js`.
 * Persists the user's selected language in `localStorage` so it survives reloads.
 */
import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { translations } from '../utils/translations'

const LanguageContext = createContext(null)

/**
 * Provider component that wraps the application and passes down string
 * dictionaries and translation helper functions to any child component.
 * 
 * @param {Object} props
 * @param {ReactNode} props.children - The child components to render within the provider.
 */
export function LanguageProvider({ children }) {
    const [language, setLanguage] = useState(() => {
        return localStorage.getItem('app_language') || 'de'
    })

    useEffect(() => {
        localStorage.setItem('app_language', language)
    }, [language])

    const value = useMemo(() => {
        return {
            language,
            setLanguage,
            t: translations[language] || translations.de,
        }
    }, [language])

    return (
        <LanguageContext.Provider value={value}>
            {children}
        </LanguageContext.Provider>
    )
}

export function useLanguage() {
    const context = useContext(LanguageContext)

    if (!context) {
        throw new Error('useLanguage must be used inside LanguageProvider')
    }

    return context
}