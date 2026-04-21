import React from 'react'
import { AlertTriangle, Check, Info, Sparkles, Wand2, X } from 'lucide-react'
import './AIAssistantUI.css'

const TITLES = {
  gap_check: 'QA Gap Check',
  rewrite: 'SOP Rewrite Preview',
  improve: 'Improvement Preview',
}

const StructuredDetails = ({ action, structuredData }) => {
  if (!structuredData) return null

  if (action === 'gap_check') {
    return (
      <div className="ai-details ai-details--amber">
        <div className="ai-details__title">
          <AlertTriangle size={18} />
          <span>Structured QA Findings</span>
        </div>
        <div className="ai-details__stack">
          <div className="ai-details__item">
            <p className="ai-details__label">Issue</p>
            <p className="ai-details__value">{structuredData.issue}</p>
          </div>
          <div className="ai-details__item">
            <p className="ai-details__label">Explanation</p>
            <p className="ai-details__value">{structuredData.explanation}</p>
          </div>
          <div className="ai-details__item">
            <p className="ai-details__label">Recommendation</p>
            <p className="ai-details__value">{structuredData.recommendation}</p>
          </div>
        </div>
      </div>
    )
  }

  if (action === 'rewrite') {
    const sections = [
      ['Purpose', structuredData.purpose],
      ['Scope', structuredData.scope],
      ['Responsibilities', structuredData.responsibilities],
      ['Documentation', structuredData.documentation],
    ]

    return (
      <div className="ai-details ai-details--green">
        <div className="ai-details__title">
          <Wand2 size={18} />
          <span>Required SOP Structure Applied</span>
        </div>
        {sections.map(([label, value]) => (
          <div key={label} className="ai-details__item">
            <p className="ai-details__label">{label}</p>
            <p className="ai-details__value">{value}</p>
          </div>
        ))}
        <div className="ai-details__item">
          <p className="ai-details__label">Procedure</p>
          <ol className="ai-details__list">
            {(structuredData.procedure || []).map((step, index) => (
              <li key={`procedure-${index}`}>{step}</li>
            ))}
          </ol>
        </div>
      </div>
    )
  }

  if (action === 'improve') {
    return (
      <div className="ai-details ai-details--violet">
        <div className="ai-details__title">
          <Sparkles size={18} />
          <span>Improvement Summary</span>
        </div>
        <div className="ai-details__item">
          <p className="ai-details__label">Improved Version</p>
          <p className="ai-details__value">{structuredData.improved_version}</p>
        </div>
        <div className="ai-details__item">
          <p className="ai-details__label">Reason for Improvement</p>
          <p className="ai-details__value">{structuredData.reason_for_improvement}</p>
        </div>
      </div>
    )
  }

  return null
}

const AIComparisonModal = ({
  isOpen,
  onClose,
  action,
  originalText,
  suggestedText,
  onAccept,
  explanation,
  structuredData,
  sectionName,
  sopTitle,
}) => {
  if (!isOpen) return null

  return (
    <div className="ai-modal-overlay">
      <div className="ai-modal">
        <div className="ai-modal__header">
          <div className="ai-modal__header-main">
            <div className="ai-modal__icon-badge">
              <SparkleIcon size={18} className="ai-modal__icon" />
            </div>
            <div>
              <h3 className="ai-modal__title">{TITLES[action] || 'AI Suggestion Review'}</h3>
              <p className="ai-modal__subtitle">
                {sopTitle || 'Untitled SOP'}
                {sectionName ? ` · ${sectionName}` : ''}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="ai-modal__close"
            aria-label="Close AI result dialog"
          >
            <X size={18} />
          </button>
        </div>

        <div className="ai-modal__body">
          {explanation && (
            <div className="ai-notes">
              <Info size={18} />
              <div>
                <p className="ai-notes__title">AI Notes</p>
                <p className="ai-notes__text">{explanation}</p>
              </div>
            </div>
          )}

          <StructuredDetails action={action} structuredData={structuredData} />

          <div className="ai-diff-grid">
            <div className="ai-diff-card">
              <div className="ai-diff-card__header">Before</div>
              <div className="ai-diff-card__content ai-diff-card__content--before">
                {originalText || 'No original text available.'}
              </div>
            </div>
            <div className="ai-diff-card">
              <div className="ai-diff-card__header ai-diff-card__header--after">After (AI Suggestion)</div>
              <div
                className="ai-diff-card__content ai-diff-card__content--after tiptap"
                dangerouslySetInnerHTML={{ __html: suggestedText || '<p>No suggestion returned.</p>' }}
              />
            </div>
          </div>
        </div>

        <div className="ai-modal__footer">
          <button
            onClick={onClose}
            className="ai-modal__button ai-modal__button--ghost"
          >
            Reject
          </button>
          <button
            onClick={onAccept}
            className="ai-modal__button ai-modal__button--primary"
          >
            <Check size={16} />
            <span>Accept and Insert</span>
          </button>
        </div>
      </div>
    </div>
  )
}

const SparkleIcon = ({ size, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M12 3c1.912 4.97 5.03 8.088 10 10-4.97 1.912-8.088 5.03-10 10-1.912-4.97-5.03-8.088-10-10 4.97-1.912 8.088-5.03 10-10Z" />
    <path d="M5 3a2 2 0 0 0 2 2" />
    <path d="M19 3a2 2 0 0 1 2 2" />
    <path d="M5 21a2 2 0 0 1 2-2" />
    <path d="M19 21a2 2 0 0 0 2-2" />
  </svg>
)

export default AIComparisonModal
