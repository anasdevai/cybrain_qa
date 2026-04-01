import React from 'react'
import { useLanguage } from '../context/LanguageContext'

export default function TopNavbar() {
    return (
        <header className="top-navbar">
            <div className="brand">
                <div className="brand-logo">Δ</div>
                <h2>AI-Law Editor</h2>
            </div>
            
            <div className="navbar-actions">
                <div className="profile-placeholder"></div>
            </div>
        </header>
    )
}
