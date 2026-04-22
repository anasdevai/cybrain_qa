import React, { useEffect, useRef, useState } from 'react'
import { Sparkles, ShieldAlert, Wand2 } from 'lucide-react'

import { performAIAction } from '../../api/editorApi'
import AIComparisonModal from './AIComparisonModal'
import './AIAssistantUI.css'

const AIAssistantBubbleMenu = ({ editor, sopMetadata, isEditable = true }) => {
  const [isAILoading, setIsAILoading] = useState(false)
  const [aiResult, setAIResult] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [menuPosition, setMenuPosition] = useState(null)
  const selectionRef = useRef(null)
  const menuRef = useRef(null)

  useEffect(() => {
    if (!editor || !isEditable) return undefined

    const updatePosition = () => {
      const { selection } = editor.state

      if (selection.empty) {
        const activeElement = document.activeElement
        if (!menuRef.current?.contains(activeElement)) {
          selectionRef.current = null
          setMenuPosition(null)
        }
        return
      }

      try {
        const { from, to } = selection
        const start = editor.view.coordsAtPos(from)
        const end = editor.view.coordsAtPos(to)
        const selectedText = editor.state.doc.textBetween(from, to, ' ').trim()

        if (!selectedText) {
          selectionRef.current = null
          setMenuPosition(null)
          return
        }

        selectionRef.current = { from, to, selectedText }
        setMenuPosition({
          top: Math.min(start.top, end.top) - 10 + window.scrollY,
          left: ((start.left + end.left) / 2) + window.scrollX,
        })
      } catch {
        selectionRef.current = null
        setMenuPosition(null)
      }
    }

    editor.on('selectionUpdate', updatePosition)
    updatePosition()

    return () => {
      editor.off('selectionUpdate', updatePosition)
    }
  }, [editor, isEditable])

  if (!editor || !isEditable) return null

  const handleAction = async (action) => {
    const savedSelection = selectionRef.current
    const selectedText = savedSelection?.selectedText || ''

    if (!selectedText) return

    let sectionName = 'Selected text'
    let sectionType = 'Paragraph'

    try {
      const resolvedPos = editor.state.doc.resolve(savedSelection.from)
      for (let depth = resolvedPos.depth; depth >= 0; depth -= 1) {
        const node = resolvedPos.node(depth)
        if (node.type.name === 'heading') {
          sectionName = node.textContent
          sectionType = 'Heading'
          break
        }
        if (node.type.name === 'table') {
          sectionType = 'Table'
        } else if (node.type.name === 'bulletList' || node.type.name === 'orderedList' || node.type.name === 'listItem') {
          sectionType = 'List'
        } else if (node.type.name === 'paragraph') {
          sectionType = 'Paragraph'
        }
      }
    } catch {
      // Best-effort section inference only.
    }

    setIsAILoading(true)
    try {
      const result = await performAIAction({
        action,
        text: selectedText,
        document_id: sopMetadata?.documentId || null,
        section_id: `${savedSelection.from}-${savedSelection.to}`,
        sop_title: sopMetadata?.title || 'Untitled SOP',
        section_name: sectionName,
        section_type: sectionType,
      })

      setAIResult({
        ...result,
        section_name: sectionName,
      })
      setIsModalOpen(true)
      setMenuPosition(null)
    } catch (err) {
      console.error('AI action failed:', err)
      alert(err.message || 'AI action failed. Please try again.')
    } finally {
      setIsAILoading(false)
    }
  }

  const handleAccept = () => {
    if (!aiResult || !selectionRef.current) return

    const { from, to } = selectionRef.current
    editor
      .chain()
      .focus()
      .deleteRange({ from, to })
      .insertContent(aiResult.suggested_text)
      .run()

    setIsModalOpen(false)
    setAIResult(null)
    selectionRef.current = null
  }

  return (
    <>
      {menuPosition ? (
        <div
          ref={menuRef}
          className="ai-action-menu"
          style={{
            top: menuPosition.top,
            left: menuPosition.left,
          }}
          onMouseDown={(event) => event.preventDefault()}
        >
          <div className="ai-action-menu__header">AI actions</div>
          <div className="ai-action-menu__actions">
            <button
              onClick={() => handleAction('gap_check')}
              className="ai-action-menu__button ai-action-menu__button--blue"
              disabled={isAILoading}
            >
              <ShieldAlert size={15} />
              <span>Gap Check</span>
            </button>

            <button
              onClick={() => handleAction('rewrite')}
              className="ai-action-menu__button ai-action-menu__button--green"
              disabled={isAILoading}
            >
              <Wand2 size={15} />
              <span>Rewrite</span>
            </button>

            <button
              onClick={() => handleAction('improve')}
              className="ai-action-menu__button ai-action-menu__button--purple"
              disabled={isAILoading}
            >
              <Sparkles size={15} />
              <span>Improve</span>
            </button>
          </div>

          {isAILoading && (
            <div className="ai-action-menu__loading">
              <div className="ai-action-menu__spinner" />
              <span>Generating suggestion...</span>
            </div>
          )}
        </div>
      ) : null}

      <AIComparisonModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setAIResult(null)
        }}
        action={aiResult?.action}
        originalText={aiResult?.original_text}
        suggestedText={aiResult?.suggested_text}
        explanation={aiResult?.explanation}
        structuredData={aiResult?.structured_data}
        onAccept={handleAccept}
        sectionName={aiResult?.section_name}
        sopTitle={sopMetadata?.title}
      />
    </>
  )
}

export default AIAssistantBubbleMenu
