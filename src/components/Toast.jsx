/**
 * Toast.jsx
 *
 * Lightweight in-app notification toast.
 * Appears in the top-right corner, auto-dismisses after `duration` ms.
 *
 * Props:
 *   message  {string}  Text to display
 *   type     {string}  'success' | 'error' | 'info'  (default: 'success')
 *   onClose  {fn}      Called when the toast should be removed
 *   duration {number}  Auto-dismiss delay in ms (default: 4000)
 */

import { useEffect } from 'react'

const ICONS = {
  success: '✓',
  error:   '✕',
  info:    'ℹ',
}

const COLORS = {
  success: { bg: '#002147', border: '#1a3f6b', icon: '#4ade80' },
  error:   { bg: '#3b0000', border: '#7f1d1d', icon: '#f87171' },
  info:    { bg: '#1a2740', border: '#334d80', icon: '#60a5fa' },
}

export default function Toast({ message, type = 'success', onClose, duration = 4000 }) {
  useEffect(() => {
    if (!message) return
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [message, onClose, duration])

  if (!message) return null

  const c = COLORS[type] || COLORS.success

  return (
    <div
      style={{
        position: 'fixed',
        top: 24,
        right: 24,
        zIndex: 99999,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
        background: c.bg,
        border: `1px solid ${c.border}`,
        borderRadius: 10,
        padding: '14px 18px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.35)',
        color: '#fff',
        fontFamily: 'var(--font-body, Manrope, sans-serif)',
        fontSize: 14,
        fontWeight: 500,
        maxWidth: 400,
        lineHeight: 1.5,
        animation: 'toastSlideIn 0.25s ease',
      }}
    >
      {/* Icon badge */}
      <span style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 26,
        height: 26,
        borderRadius: '50%',
        background: c.icon,
        color: '#000',
        fontWeight: 800,
        fontSize: 13,
        flexShrink: 0,
        marginTop: 1,
      }}>
        {ICONS[type]}
      </span>

      {/* Message */}
      <span style={{ flex: 1 }}>{message}</span>

      {/* Close button */}
      <button
        onClick={onClose}
        style={{
          background: 'none',
          border: 'none',
          color: 'rgba(255,255,255,0.5)',
          cursor: 'pointer',
          fontSize: 18,
          lineHeight: 1,
          padding: 0,
          marginTop: -1,
          flexShrink: 0,
        }}
        title="Dismiss"
      >
        ×
      </button>

      <style>{`
        @keyframes toastSlideIn {
          from { opacity: 0; transform: translateY(-12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
