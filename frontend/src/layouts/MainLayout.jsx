import React, { useState, useEffect, useCallback } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from '../components/Layout/Sidebar'
import Topbar from '../components/Layout/Topbar'
import AIWidget from '../components/Dashboard/AIWidget'
import FloatingAskAIButton from '../components/Common/FloatingAskAIButton'
import './MainLayout.css'

/**
 * MainLayout
 *
 * 3-column responsive structure:
 * 1. Sidebar — fixed width on desktop, fixed drawer on mobile (≤1024px)
 * 2. Main Content — fluid
 * 3. AI Assistant Widget — right column on desktop, slide-out drawer on mobile
 */
export default function MainLayout() {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [aiWidgetOpen, setAiWidgetOpen] = useState(false)

  const showAIWidget = ['/', '/dashboard', '/sops', '/knowledge'].includes(location.pathname)

  // Close drawers on route change
  useEffect(() => {
    setSidebarOpen(false)
    setAiWidgetOpen(false)
  }, [location.pathname])

  // Prevent body scroll when either drawer is open
  useEffect(() => {
    document.body.style.overflow = (sidebarOpen || aiWidgetOpen) ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [sidebarOpen, aiWidgetOpen])

  const handleToggleAiWidget = useCallback(() => {
    setAiWidgetOpen(prev => !prev)
  }, [])

  const handleCloseAiWidget = useCallback(() => {
    setAiWidgetOpen(false)
  }, [])

  const layoutClass = [
    'main-layout-container',
    !showAIWidget ? 'main-layout--no-ai' : ''
  ].filter(Boolean).join(' ')

  return (
    <div className={layoutClass}>
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className="main-content-area">
        <Topbar onMenuToggle={() => setSidebarOpen(prev => !prev)} />
        <div className="page-outlet">
          <Outlet />
        </div>
      </main>

      {/* AI Widget — always in DOM for pages that use it; visible on desktop, drawer on mobile */}
      {showAIWidget && (
        <aside className={`ai-assistant-sidebar${aiWidgetOpen ? ' ai-sidebar-open' : ''}`}>
          <AIWidget />
        </aside>
      )}

      {/* Sidebar overlay — closes left sidebar on tap outside */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* AI Widget overlay — closes right AI drawer on tap outside (mobile only) */}
      {aiWidgetOpen && showAIWidget && (
        <div
          className="ai-widget-overlay"
          onClick={handleCloseAiWidget}
          aria-hidden="true"
        />
      )}

      <FloatingAskAIButton onClick={handleToggleAiWidget} isOpen={aiWidgetOpen} />
    </div>
  )
}
