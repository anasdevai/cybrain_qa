import React from 'react'
import './SourceTag.css'

/**
 * SourceTag — Colored reference badge for SOPs, DEVs, CAPAs, etc.
 * @param {{ label: string, type?: string, size?: string, showDot?: boolean }} props
 */
export default function SourceTag({ label, type = 'generic', size = '', showDot = true }) {
  const className = [
    'source-tag',
    `source-tag--${type}`,
    size ? `source-tag--${size}` : ''
  ].filter(Boolean).join(' ')

  return (
    <span className={className} title={label}>
      {showDot && <span className="source-tag__dot" />}
      {label}
    </span>
  )
}
